from django.contrib.auth.models import AnonymousUser
from rest_framework import status, views, viewsets
from rest_framework.decorators import action
from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from rest_framework_simplejwt.views import TokenRefreshView

import redis
from authentication.choices import *
from authentication.models import User
from authentication.permissions import AnonymousTokenPermission
from authentication.v1.serializers import (GetVerificationCodeSerializer,
                                           LoginSerializer)
from authentication.v1.utils.otp import create_verification_code
from authentication.v1.utils.otp import load_otp_adapter_lazy as OTPAdapter
from authentication.v1.utils.token import generate_token
from authentication.v1.utils.utils import normilize_phone_number
from authentication.validators import (PhoneNumberValidatorAdapter,
                                       country_code_validator)
from common import variables
from common.utils import BaseResponse, BaseTime
from common.validators import check_api_input_data
from common.variables import *
from common.variables import BUSINESS_STATUS
from common.utils import countries_hints_dict


def login_otp_validator(user, validated_verification_code, original_otp_data, serializer):
    """
    Check the validity of the provided OTP against the stored OTP.

    Parameters
    ----------
    validated_phone_number : str
        The validated phone number of the user.
    validated_verification_code : str
        The verification code provided by the user.
    serializer : Serializer
        The serializer instance used to interact with the OTP data.
    """
    if original_otp_data:
        original_otp, exp_str = original_otp_data[
            variables.VERIFICATION_CODE], original_otp_data[variables.EXPIRTION_TIME]
    else:
        return False

    if str(original_otp).strip() != str(validated_verification_code).strip():
        return False

    now = BaseTime().now()

    if exp_str:
        if exp_str < now:
            return False
    else:
        False
    return True


def get_token_for_user(user, serializer, request):
    """
    Generate authentication tokens for the user.

    Parameters
    ----------
    user : User
        The user instance for whom the tokens are to be generated.
    serializer : Serializer
        The serializer instance used to interact with user data.
    request : Request
        The HTTP request object.

    Returns
    -------
    dict
        A dictionary containing the generated authentication tokens.
    """
    if user.state == variables.PENDING:
        serializer.set_state(user, variables.PHONE_VERIFIED)
    tokens = generate_token(request, user)
    return tokens


def send_otp(
        phone_number, verification_code):
    """
    Generate and send a verification code (OTP) to the user.

    Parameters
    ----------
    phone_number : str
        The phone number to which the OTP is to be sent.
    user : User
        The user instance for whom the OTP is to be generated.
    serializer : Serializer
        The serializer instance used to interact with OTP data.

    Returns
    -------
    None
    """
    OTPAdapter().send_otp(phone_number=phone_number, otp=verification_code)


class VerificationCodeViewSet(
    viewsets.GenericViewSet,
):
    permission_classes = [AnonymousTokenPermission]
    queryset = User.objects.all()
    serializer_class = GetVerificationCodeSerializer

    @action(detail=False, methods=[variables.POST])
    def get(self, request):
        """
        Retrieves or generates a verification code for a given phone number.

        This endpoint is used to retrieve or generate a verification code for a provided phone number. 
        If the phone number is associated with an existing user, a verification code is sent. 
        If the phone number is not associated with any existing user, a new user is created and a verification code is sent.

        Parameters
        -------
        request `Request`: The HTTP request object containing the phone_number in the data field.

        Returns
        -------
        Response: A response indicating the success or failure of the operation.
        """

        # Check input data
        required_fields = [variables.PHONE_NUMBER, variables.COUNTRY_CODE]
        if not check_api_input_data(request, required_fields):
            return Response(status=status.HTTP_400_BAD_REQUEST, exception=True, data=INVALID_INPUT_DATA)

        # Validate Input data
        phone_number = request.data.get(variables.PHONE_NUMBER)
        country_code = request.data.get(variables.COUNTRY_CODE)
        if not country_code_validator(country_code):
            return Response(status=status.HTTP_400_BAD_REQUEST, exception=True, data=INVALID_INPUT_DATA)
        if not PhoneNumberValidatorAdapter(phone_number, country_code).validate():
            return BaseResponse(
                http_status_code=status.HTTP_400_BAD_REQUEST,
                is_exception=True,
                message=f"{INVALID_PHONE_NUMBER}. The supported formet for selected country is: {countries_hints_dict[country_code]}",
                data=None,
                business_status_code=BUSINESS_STATUS.INVALID_INPUT_DATA,
            )
        normalized_phone_number = normilize_phone_number(
            phone_number, country_code=country_code)
        validated_data = {
            variables.PHONE_NUMBER: normalized_phone_number,
            variables.COUNTRY_CODE: country_code
        }

        # Send data to serializer
        serializer = self.get_serializer_class()(data=validated_data)
        if not serializer.is_valid():
            return BaseResponse(
                message=INVALID_INPUT_DATA,
                data={variables.DETAILS: serializer.errors},
                is_exception=True,
                http_status_code=status.HTTP_400_BAD_REQUEST,
                business_status_code=BUSINESS_STATUS.INVALID_INPUT_DATA,
            )

        # Send Verification code
        user = serializer.user_exists(
            phone_number=normalized_phone_number)  # returns user or none
        if user:
            if user.is_bocked:
                return BaseResponse(
                    message=BLOCKED_USER,
                    data=None,
                    is_exception=True,
                    http_status_code=status.HTTP_200_OK,
                    business_status_code=BUSINESS_STATUS.USER_IS_BLOCKED,
                )
            try:
                if not serializer.have_access_to_request_otp(user):
                    return Response(status=status.HTTP_429_TOO_MANY_REQUESTS)
            except redis.ConnectionError:
                # TODO add this to a log server
                return BaseResponse(
                    data=None,
                    message=variables.TRY_AGAIN_LATER,
                    is_exception=True,
                    business_status_code=BUSINESS_STATUS.REDIS_IS_DOWN,
                    http_status_code=status.HTTP_200_OK
                )
            verification_code, exp = create_verification_code(request.user)
            send_otp(phone_number=normalized_phone_number,
                     verification_code=verification_code)
            try:
                serializer.add_otp_to_redis(user, verification_code, exp)
            except redis.ConnectionError:
                return BaseResponse(
                    data=None,
                    message=variables.TRY_AGAIN_LATER,
                    is_exception=True,
                    business_status_code=BUSINESS_STATUS.REDIS_IS_DOWN,
                    http_status_code=status.HTTP_200_OK
                )

            return BaseResponse(
                message=VERIFICATION_CODE_SENDED,
                data=None,
                is_exception=False,
                http_status_code=status.HTTP_200_OK,
                business_status_code=BUSINESS_STATUS.SUCCESS,
            )
        else:
            # sign_up_event_adapter(created=True, phone_number=normalized_phone_number)
            user = serializer.create_user(phone_number=normalized_phone_number)
            verification_code, exp = create_verification_code(request.user)
            send_otp(phone_number=normalized_phone_number,
                     verification_code=verification_code)
            return BaseResponse(
                message=USER_REGISTERD,
                data=None,
                is_exception=False,
                http_status_code=status.HTTP_201_CREATED,
                business_status_code=BUSINESS_STATUS.SUCCESS,
            )


class AnonymousUserViewSet(viewsets.ViewSet):
    permission_classes = [AllowAny]

    @action(detail=False, methods=['get'])
    def generate_token(self, request):
        """
        Generate and return an anonymous access token.

        Parameters:
        ----------
        request: HttpRequest
            The Django HttpRequest object.

        Returns:
        ----------
        Response
            The response containing the generated anonymous access token.
        """
        if not isinstance(request.user, AnonymousUser):
            return BaseResponse(
                message=MUST_BE_ANON,
                data=None,
                is_exception=True,
                http_status_code=status.HTTP_400_BAD_REQUEST,
                business_status_code=BUSINESS_STATUS.USER_DONT_HAVE_ACCESS,
            )
        try:
            access = generate_token(request)[variables.ANON_TOKEN]
            return BaseResponse(
                message=ANON_TOKEN_CREATED,
                data=access,
                is_exception=False,
                http_status_code=status.HTTP_200_OK,
                business_status_code=BUSINESS_STATUS.SUCCESS,
            )
        except Exception as e:
            return Response(
                data=str(e),
                is_exception=True,
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )


class LoginViewSet(
    viewsets.GenericViewSet,
):
    """
    API endpoint that provides various actions related to Login.

    Attributes
    ----------
    * `queryset`: ``QuerySet``
        The set of all User objects.
    """
    queryset = User.objects.all()
    permission_classes = [AnonymousTokenPermission]
    serializer_class = LoginSerializer

    @action(detail=False, methods=[variables.POST])
    def login(self, request):
        """
        Logs in a user by verifying the provided phone number and verification code.

        This endpoint is used to log in a user by verifying the provided phone number and verification code against stored data.
        If the verification is successful, authentication tokens are generated and returned.

        Parameters
        ----------
        request : Request
            The HTTP request object containing the phone_number and verification_code in the data field.

        Returns
        -------
        Response
            A response indicating the success or failure of the login operation, along with authentication tokens if successful.
        """

        # Check input data
        required_fields = [variables.PHONE_NUMBER,
                           variables.VERIFICATION_CODE, variables.COUNTRY_CODE]
        if not check_api_input_data(request, required_fields):
            return Response(status=status.HTTP_400_BAD_REQUEST, exception=True, data=INVALID_INPUT_DATA)

        # Validate Input data
        phone_number = request.data.get(variables.PHONE_NUMBER)
        country_code = request.data.get(variables.COUNTRY_CODE)
        if not country_code_validator(country_code):
            return Response(status=status.HTTP_400_BAD_REQUEST, exception=True, data=INVALID_INPUT_DATA)
        if not PhoneNumberValidatorAdapter(phone_number, country_code).validate():
            return BaseResponse(
                http_status_code=status.HTTP_400_BAD_REQUEST,
                is_exception=True,
                message=f"{INVALID_PHONE_NUMBER}. The supported formet for selected country is: {countries_hints_dict[country_code]}",
                data=None,
                business_status_code=BUSINESS_STATUS.INVALID_INPUT_DATA,
            )
        normalized_phone_number = normilize_phone_number(
            phone_number, country_code)
        verification_code = request.data.get(variables.VERIFICATION_CODE)
        validated_data = {
            variables.PHONE_NUMBER: normalized_phone_number,
            variables.COUNTRY_CODE: country_code,
            variables.VERIFICATION_CODE: verification_code}

        # Send data to serializer
        serializer = self.get_serializer_class()(data=validated_data)
        if not serializer.is_valid():
            return BaseResponse(
                message=INVALID_INPUT_DATA,
                data={variables.DETAILS: serializer.errors},
                is_exception=True,
                http_status_code=status.HTTP_400_BAD_REQUEST,
                business_status_code=BUSINESS_STATUS.INVALID_INPUT_DATA,
            )

        # Send access token
        user = serializer.user_exists(phone_number=normalized_phone_number)
        if not user:
            return BaseResponse(
                message=USER_DOSE_NOT_EXISTS,
                data=None,
                is_exception=True,
                http_status_code=status.HTTP_200_OK,
                business_status_code=BUSINESS_STATUS.USER_NOT_FOUND,)

        if user.is_bocked:
            return BaseResponse(
                message=BLOCKED_USER,
                data=None,
                is_exception=True,
                http_status_code=status.HTTP_200_OK,
                business_status_code=BUSINESS_STATUS.USER_IS_BLOCKED,
            )
        try:
            original_otp_data = serializer.get_original_otp(user)
        except redis.ConnectionError:
            # TODO add this to a log server
            return BaseResponse(
                data=None,
                message=variables.TRY_AGAIN_LATER,
                is_exception=True,
                business_status_code=BUSINESS_STATUS.REDIS_IS_DOWN,
                http_status_code=status.HTTP_200_OK
            )
        if not login_otp_validator(user, validated_data[variables.VERIFICATION_CODE], original_otp_data, serializer):
            return BaseResponse(
                message=INVALID_OTP,
                is_exception=True,
                http_status_code=status.HTTP_200_OK,
                business_status_code=BUSINESS_STATUS.INVALID_LOGIN_CREDENTIONAL,)

        tokens = get_token_for_user(user, serializer, request)
        try:
            serializer.remove_otp_from_redis(user)
        except redis.ConnectionError:
            return BaseResponse(
                data=None,
                message=variables.TRY_AGAIN_LATER,
                is_exception=True,
                business_status_code=BUSINESS_STATUS.REDIS_IS_DOWN,
                http_status_code=status.HTTP_200_OK
            )
        return BaseResponse(
            message=USER_LOGGED_IN,
            data={
                variables.REFRESH_TOKEN: str(tokens[variables.REFRESH]),
                variables.ACCESS_TOKEN: str(tokens[variables.ACCESS]),
            },
            is_exception=False,
            http_status_code=status.HTTP_200_OK,
            business_status_code=BUSINESS_STATUS.SUCCESS,)

    @action(detail=False, methods=[variables.POST], serializer_class=None)
    def logout(self, request):
        """
        Log out the current user.

        Parameters:
        ----------
        * `request`: ``HttpRequest``
            The Django HttpRequest object.

        Returns:
        ----------
        ``Response``
            The response indicating the success or failure of the logout process.
        """
        if isinstance(request.user, AnonymousUser):
            return Response(status=status.HTTP_400_BAD_REQUEST, data=None)

        return BaseResponse(
            message=USER_LOGGED_OUT,
            data=None,
            is_exception=False,
            http_status_code=status.HTTP_200_OK,
            business_status_code=BUSINESS_STATUS.SUCCESS,
        )


class TokenRefreshWithPermission(TokenRefreshView):
    """
    Token refresh view with anonymous token permission.

    Attributes:
    ----------
    * `permission_classes`: ``list``
        List of permissions required for token refresh.
    """
    permission_classes = [AnonymousTokenPermission]
