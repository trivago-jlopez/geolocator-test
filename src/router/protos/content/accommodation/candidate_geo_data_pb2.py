# Generated by the protocol buffer compiler.  DO NOT EDIT!
# source: content.accommodation.candidate_geo_data.proto

import sys
_b=sys.version_info[0]<3 and (lambda x:x) or (lambda x:x.encode('latin1'))
from google.protobuf import descriptor as _descriptor
from google.protobuf import message as _message
from google.protobuf import reflection as _reflection
from google.protobuf import symbol_database as _symbol_database
from google.protobuf import descriptor_pb2
# @@protoc_insertion_point(imports)

_sym_db = _symbol_database.Default()




DESCRIPTOR = _descriptor.FileDescriptor(
  name='content.accommodation.candidate_geo_data.proto',
  package='com.trivago.streaming.toolkit.proto.content.accommodation',
  syntax='proto2',
  serialized_pb=_b('\n.content.accommodation.candidate_geo_data.proto\x12\x39\x63om.trivago.streaming.toolkit.proto.content.accommodation\"\xe7\x02\n\x12\x63\x61ndidate_geo_data\x12]\n\x03key\x18\x02 \x01(\x0b\x32P.com.trivago.streaming.toolkit.proto.content.accommodation.candidate_geo_data.PK\x12\x13\n\x0blocality_id\x18\x03 \x01(\r\x12\x13\n\x0blocality_ns\x18\x04 \x01(\r\x12\"\n\x1a\x61\x64ministrative_division_id\x18\x05 \x01(\r\x12\"\n\x1a\x61\x64ministrative_division_ns\x18\x06 \x01(\r\x12\x12\n\ncountry_id\x18\x07 \x01(\r\x12\x12\n\ncountry_ns\x18\x08 \x01(\r\x12\x11\n\tlongitude\x18\t \x01(\x01\x12\x10\n\x08latitude\x18\n \x01(\x01\x12\x17\n\x0fvalid_geo_point\x18\x0b \x01(\x08\x1a\x1a\n\x02PK\x12\x14\n\x0c\x63\x61ndidate_id\x18\x01 \x01(\rB\x99\x01\n>com.trivago.streaming.toolkit.proto.content.candidate_geo_dataB\x17\x63\x61ndidate_geo_dataOuterZ>com.trivago.streaming.toolkit.proto.content.candidate_geo_data')
)




_CANDIDATE_GEO_DATA_PK = _descriptor.Descriptor(
  name='PK',
  full_name='com.trivago.streaming.toolkit.proto.content.accommodation.candidate_geo_data.PK',
  filename=None,
  file=DESCRIPTOR,
  containing_type=None,
  fields=[
    _descriptor.FieldDescriptor(
      name='candidate_id', full_name='com.trivago.streaming.toolkit.proto.content.accommodation.candidate_geo_data.PK.candidate_id', index=0,
      number=1, type=13, cpp_type=3, label=1,
      has_default_value=False, default_value=0,
      message_type=None, enum_type=None, containing_type=None,
      is_extension=False, extension_scope=None,
      options=None, file=DESCRIPTOR),
  ],
  extensions=[
  ],
  nested_types=[],
  enum_types=[
  ],
  options=None,
  is_extendable=False,
  syntax='proto2',
  extension_ranges=[],
  oneofs=[
  ],
  serialized_start=443,
  serialized_end=469,
)

_CANDIDATE_GEO_DATA = _descriptor.Descriptor(
  name='candidate_geo_data',
  full_name='com.trivago.streaming.toolkit.proto.content.accommodation.candidate_geo_data',
  filename=None,
  file=DESCRIPTOR,
  containing_type=None,
  fields=[
    _descriptor.FieldDescriptor(
      name='key', full_name='com.trivago.streaming.toolkit.proto.content.accommodation.candidate_geo_data.key', index=0,
      number=2, type=11, cpp_type=10, label=1,
      has_default_value=False, default_value=None,
      message_type=None, enum_type=None, containing_type=None,
      is_extension=False, extension_scope=None,
      options=None, file=DESCRIPTOR),
    _descriptor.FieldDescriptor(
      name='locality_id', full_name='com.trivago.streaming.toolkit.proto.content.accommodation.candidate_geo_data.locality_id', index=1,
      number=3, type=13, cpp_type=3, label=1,
      has_default_value=False, default_value=0,
      message_type=None, enum_type=None, containing_type=None,
      is_extension=False, extension_scope=None,
      options=None, file=DESCRIPTOR),
    _descriptor.FieldDescriptor(
      name='locality_ns', full_name='com.trivago.streaming.toolkit.proto.content.accommodation.candidate_geo_data.locality_ns', index=2,
      number=4, type=13, cpp_type=3, label=1,
      has_default_value=False, default_value=0,
      message_type=None, enum_type=None, containing_type=None,
      is_extension=False, extension_scope=None,
      options=None, file=DESCRIPTOR),
    _descriptor.FieldDescriptor(
      name='administrative_division_id', full_name='com.trivago.streaming.toolkit.proto.content.accommodation.candidate_geo_data.administrative_division_id', index=3,
      number=5, type=13, cpp_type=3, label=1,
      has_default_value=False, default_value=0,
      message_type=None, enum_type=None, containing_type=None,
      is_extension=False, extension_scope=None,
      options=None, file=DESCRIPTOR),
    _descriptor.FieldDescriptor(
      name='administrative_division_ns', full_name='com.trivago.streaming.toolkit.proto.content.accommodation.candidate_geo_data.administrative_division_ns', index=4,
      number=6, type=13, cpp_type=3, label=1,
      has_default_value=False, default_value=0,
      message_type=None, enum_type=None, containing_type=None,
      is_extension=False, extension_scope=None,
      options=None, file=DESCRIPTOR),
    _descriptor.FieldDescriptor(
      name='country_id', full_name='com.trivago.streaming.toolkit.proto.content.accommodation.candidate_geo_data.country_id', index=5,
      number=7, type=13, cpp_type=3, label=1,
      has_default_value=False, default_value=0,
      message_type=None, enum_type=None, containing_type=None,
      is_extension=False, extension_scope=None,
      options=None, file=DESCRIPTOR),
    _descriptor.FieldDescriptor(
      name='country_ns', full_name='com.trivago.streaming.toolkit.proto.content.accommodation.candidate_geo_data.country_ns', index=6,
      number=8, type=13, cpp_type=3, label=1,
      has_default_value=False, default_value=0,
      message_type=None, enum_type=None, containing_type=None,
      is_extension=False, extension_scope=None,
      options=None, file=DESCRIPTOR),
    _descriptor.FieldDescriptor(
      name='longitude', full_name='com.trivago.streaming.toolkit.proto.content.accommodation.candidate_geo_data.longitude', index=7,
      number=9, type=1, cpp_type=5, label=1,
      has_default_value=False, default_value=float(0),
      message_type=None, enum_type=None, containing_type=None,
      is_extension=False, extension_scope=None,
      options=None, file=DESCRIPTOR),
    _descriptor.FieldDescriptor(
      name='latitude', full_name='com.trivago.streaming.toolkit.proto.content.accommodation.candidate_geo_data.latitude', index=8,
      number=10, type=1, cpp_type=5, label=1,
      has_default_value=False, default_value=float(0),
      message_type=None, enum_type=None, containing_type=None,
      is_extension=False, extension_scope=None,
      options=None, file=DESCRIPTOR),
    _descriptor.FieldDescriptor(
      name='valid_geo_point', full_name='com.trivago.streaming.toolkit.proto.content.accommodation.candidate_geo_data.valid_geo_point', index=9,
      number=11, type=8, cpp_type=7, label=1,
      has_default_value=False, default_value=False,
      message_type=None, enum_type=None, containing_type=None,
      is_extension=False, extension_scope=None,
      options=None, file=DESCRIPTOR),
  ],
  extensions=[
  ],
  nested_types=[_CANDIDATE_GEO_DATA_PK, ],
  enum_types=[
  ],
  options=None,
  is_extendable=False,
  syntax='proto2',
  extension_ranges=[],
  oneofs=[
  ],
  serialized_start=110,
  serialized_end=469,
)

_CANDIDATE_GEO_DATA_PK.containing_type = _CANDIDATE_GEO_DATA
_CANDIDATE_GEO_DATA.fields_by_name['key'].message_type = _CANDIDATE_GEO_DATA_PK
DESCRIPTOR.message_types_by_name['candidate_geo_data'] = _CANDIDATE_GEO_DATA
_sym_db.RegisterFileDescriptor(DESCRIPTOR)

candidate_geo_data = _reflection.GeneratedProtocolMessageType('candidate_geo_data', (_message.Message,), dict(

  PK = _reflection.GeneratedProtocolMessageType('PK', (_message.Message,), dict(
    DESCRIPTOR = _CANDIDATE_GEO_DATA_PK,
    __module__ = 'content.accommodation.candidate_geo_data_pb2'
    # @@protoc_insertion_point(class_scope:com.trivago.streaming.toolkit.proto.content.accommodation.candidate_geo_data.PK)
    ))
  ,
  DESCRIPTOR = _CANDIDATE_GEO_DATA,
  __module__ = 'content.accommodation.candidate_geo_data_pb2'
  # @@protoc_insertion_point(class_scope:com.trivago.streaming.toolkit.proto.content.accommodation.candidate_geo_data)
  ))
_sym_db.RegisterMessage(candidate_geo_data)
_sym_db.RegisterMessage(candidate_geo_data.PK)


DESCRIPTOR.has_options = True
DESCRIPTOR._options = _descriptor._ParseOptions(descriptor_pb2.FileOptions(), _b('\n>com.trivago.streaming.toolkit.proto.content.candidate_geo_dataB\027candidate_geo_dataOuterZ>com.trivago.streaming.toolkit.proto.content.candidate_geo_data'))
# @@protoc_insertion_point(module_scope)
