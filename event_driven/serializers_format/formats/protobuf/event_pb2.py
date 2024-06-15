# -*- coding: utf-8 -*-
# Generated by the protocol buffer compiler.  DO NOT EDIT!
# source: event.proto

from google.protobuf import descriptor as _descriptor
from google.protobuf import message as _message
from google.protobuf import reflection as _reflection
from google.protobuf import symbol_database as _symbol_database

# @@protoc_insertion_point(imports)

_sym_db = _symbol_database.Default()


DESCRIPTOR = _descriptor.FileDescriptor(
    name='event.proto',
    package='',
    syntax='proto3',
    serialized_options=None,
    create_key=_descriptor._internal_create_key,
    serialized_pb=b'\n\x0b\x65vent.proto\"v\n\x08logevent\x12\x0c\n\x04name\x18\x01 \x01(\t\x12\x11\n\ttimestamp\x18\x02 \x01(\t\x12\x0e\n\x06source\x18\x03 \x01(\t\x12\x19\n\x11serializer_format\x18\x04 \x01(\t\x12\x0f\n\x07message\x18\x05 \x01(\t\x12\r\n\x05level\x18\x06 \x01(\tb\x06proto3'
)


_LOGEVENT = _descriptor.Descriptor(
    name='logevent',
    full_name='logevent',
    filename=None,
    file=DESCRIPTOR,
    containing_type=None,
    create_key=_descriptor._internal_create_key,
    fields=[
        _descriptor.FieldDescriptor(
            name='name', full_name='logevent.name', index=0,
            number=1, type=9, cpp_type=9, label=1,
            has_default_value=False, default_value=b"".decode('utf-8'),
            message_type=None, enum_type=None, containing_type=None,
            is_extension=False, extension_scope=None,
            serialized_options=None, file=DESCRIPTOR,  create_key=_descriptor._internal_create_key),
        _descriptor.FieldDescriptor(
            name='timestamp', full_name='logevent.timestamp', index=1,
            number=2, type=9, cpp_type=9, label=1,
            has_default_value=False, default_value=b"".decode('utf-8'),
            message_type=None, enum_type=None, containing_type=None,
            is_extension=False, extension_scope=None,
            serialized_options=None, file=DESCRIPTOR,  create_key=_descriptor._internal_create_key),
        _descriptor.FieldDescriptor(
            name='source', full_name='logevent.source', index=2,
            number=3, type=9, cpp_type=9, label=1,
            has_default_value=False, default_value=b"".decode('utf-8'),
            message_type=None, enum_type=None, containing_type=None,
            is_extension=False, extension_scope=None,
            serialized_options=None, file=DESCRIPTOR,  create_key=_descriptor._internal_create_key),
        _descriptor.FieldDescriptor(
            name='serializer_format', full_name='logevent.serializer_format', index=3,
            number=4, type=9, cpp_type=9, label=1,
            has_default_value=False, default_value=b"".decode('utf-8'),
            message_type=None, enum_type=None, containing_type=None,
            is_extension=False, extension_scope=None,
            serialized_options=None, file=DESCRIPTOR,  create_key=_descriptor._internal_create_key),
        _descriptor.FieldDescriptor(
            name='message', full_name='logevent.message', index=4,
            number=5, type=9, cpp_type=9, label=1,
            has_default_value=False, default_value=b"".decode('utf-8'),
            message_type=None, enum_type=None, containing_type=None,
            is_extension=False, extension_scope=None,
            serialized_options=None, file=DESCRIPTOR,  create_key=_descriptor._internal_create_key),
        _descriptor.FieldDescriptor(
            name='level', full_name='logevent.level', index=5,
            number=6, type=9, cpp_type=9, label=1,
            has_default_value=False, default_value=b"".decode('utf-8'),
            message_type=None, enum_type=None, containing_type=None,
            is_extension=False, extension_scope=None,
            serialized_options=None, file=DESCRIPTOR,  create_key=_descriptor._internal_create_key),
    ],
    extensions=[
    ],
    nested_types=[],
    enum_types=[
    ],
    serialized_options=None,
    is_extendable=False,
    syntax='proto3',
    extension_ranges=[],
    oneofs=[
    ],
    serialized_start=15,
    serialized_end=133,
)

DESCRIPTOR.message_types_by_name['logevent'] = _LOGEVENT
_sym_db.RegisterFileDescriptor(DESCRIPTOR)

logevent = _reflection.GeneratedProtocolMessageType('logevent', (_message.Message,), {
    'DESCRIPTOR': _LOGEVENT,
    '__module__': 'event_pb2'
    # @@protoc_insertion_point(class_scope:logevent)
})
_sym_db.RegisterMessage(logevent)


# @@protoc_insertion_point(module_scope)