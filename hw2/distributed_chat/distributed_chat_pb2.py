# -*- coding: utf-8 -*-
# Generated by the protocol buffer compiler.  DO NOT EDIT!
# NO CHECKED-IN PROTOBUF GENCODE
# source: distributed_chat/distributed_chat.proto
# Protobuf Python Version: 5.29.0
"""Generated protocol buffer code."""
from google.protobuf import descriptor as _descriptor
from google.protobuf import descriptor_pool as _descriptor_pool
from google.protobuf import runtime_version as _runtime_version
from google.protobuf import symbol_database as _symbol_database
from google.protobuf.internal import builder as _builder
_runtime_version.ValidateProtobufRuntimeVersion(
    _runtime_version.Domain.PUBLIC,
    5,
    29,
    0,
    '',
    'distributed_chat/distributed_chat.proto'
)
# @@protoc_insertion_point(imports)

_sym_db = _symbol_database.Default()




DESCRIPTOR = _descriptor_pool.Default().AddSerializedFile(b'\n\'distributed_chat/distributed_chat.proto\x12\x10\x64istributed_chat\"5\n\x0fUserCredentials\x12\x10\n\x08username\x18\x01 \x01(\t\x12\x10\n\x08password\x18\x02 \x01(\t\"\x1c\n\x08Username\x12\x10\n\x08username\x18\x01 \x01(\t\",\n\x08Response\x12\x0f\n\x07success\x18\x01 \x01(\x08\x12\x0f\n\x07message\x18\x02 \x01(\t\"G\n\rLoginResponse\x12\x0f\n\x07success\x18\x01 \x01(\x08\x12\x0f\n\x07message\x18\x02 \x01(\t\x12\x14\n\x0cunread_count\x18\x03 \x01(\x05\"C\n\x07\x41\x63\x63ount\x12\x10\n\x08username\x18\x01 \x01(\t\x12\x12\n\ncreated_at\x18\x02 \x01(\t\x12\x12\n\nlast_login\x18\x03 \x01(\t\"E\n\x12\x41\x63\x63ountListRequest\x12\x0f\n\x07pattern\x18\x01 \x01(\t\x12\x0c\n\x04page\x18\x02 \x01(\x05\x12\x10\n\x08per_page\x18\x03 \x01(\x05\"b\n\x13\x41\x63\x63ountListResponse\x12+\n\x08\x61\x63\x63ounts\x18\x01 \x03(\x0b\x32\x19.distributed_chat.Account\x12\x0c\n\x04page\x18\x02 \x01(\x05\x12\x10\n\x08per_page\x18\x03 \x01(\x05\"j\n\x07Message\x12\n\n\x02id\x18\x01 \x01(\x03\x12\x0e\n\x06sender\x18\x02 \x01(\t\x12\x11\n\trecipient\x18\x03 \x01(\t\x12\x0f\n\x07\x63ontent\x18\x04 \x01(\t\x12\x11\n\ttimestamp\x18\x05 \x01(\t\x12\x0c\n\x04read\x18\x06 \x01(\x08\"1\n\x0eMessageRequest\x12\x10\n\x08username\x18\x01 \x01(\t\x12\r\n\x05\x63ount\x18\x02 \x01(\x05\":\n\x0bMessageList\x12+\n\x08messages\x18\x01 \x03(\x0b\x32\x19.distributed_chat.Message\"=\n\x14\x44\x65leteMessageRequest\x12\x10\n\x08username\x18\x01 \x01(\t\x12\x13\n\x0bmessage_ids\x18\x02 \x03(\x03\":\n\x11MarkAsReadRequest\x12\x10\n\x08username\x18\x01 \x01(\t\x12\x13\n\x0bmessage_ids\x18\x02 \x03(\x03\"`\n\x0bVoteRequest\x12\x0c\n\x04term\x18\x01 \x01(\x05\x12\x14\n\x0c\x63\x61ndidate_id\x18\x02 \x01(\t\x12\x16\n\x0elast_log_index\x18\x03 \x01(\x03\x12\x15\n\rlast_log_term\x18\x04 \x01(\x05\"2\n\x0cVoteResponse\x12\x0c\n\x04term\x18\x01 \x01(\x05\x12\x14\n\x0cvote_granted\x18\x02 \x01(\x08\"K\n\x08LogEntry\x12\x0c\n\x04term\x18\x01 \x01(\x05\x12\r\n\x05index\x18\x02 \x01(\x03\x12\x0c\n\x04\x64\x61ta\x18\x03 \x01(\x0c\x12\x14\n\x0c\x63ommand_type\x18\x04 \x01(\t\"\xaa\x01\n\x14\x41ppendEntriesRequest\x12\x0c\n\x04term\x18\x01 \x01(\x05\x12\x11\n\tleader_id\x18\x02 \x01(\t\x12\x16\n\x0eprev_log_index\x18\x03 \x01(\x03\x12\x15\n\rprev_log_term\x18\x04 \x01(\x05\x12+\n\x07\x65ntries\x18\x05 \x03(\x0b\x32\x1a.distributed_chat.LogEntry\x12\x15\n\rleader_commit\x18\x06 \x01(\x03\"K\n\x15\x41ppendEntriesResponse\x12\x0c\n\x04term\x18\x01 \x01(\x05\x12\x0f\n\x07success\x18\x02 \x01(\x08\x12\x13\n\x0bmatch_index\x18\x03 \x01(\x03\"3\n\x0bSyncRequest\x12\x12\n\nfrom_index\x18\x01 \x01(\x03\x12\x10\n\x08to_index\x18\x02 \x01(\x03\"L\n\x0cSyncResponse\x12+\n\x07\x65ntries\x18\x01 \x03(\x0b\x32\x1a.distributed_chat.LogEntry\x12\x0f\n\x07success\x18\x02 \x01(\x08\"F\n\x0fGetStateRequest\x12\x1b\n\x13include_log_entries\x18\x01 \x01(\x08\x12\x16\n\x0e\x66rom_log_index\x18\x02 \x01(\x03\"\xa6\x01\n\rStateResponse\x12\x14\n\x0c\x63urrent_term\x18\x01 \x01(\x05\x12\x11\n\tvoted_for\x18\x02 \x01(\t\x12\x14\n\x0c\x63ommit_index\x18\x03 \x01(\x03\x12\x14\n\x0clast_applied\x18\x04 \x01(\x03\x12/\n\x0blog_entries\x18\x05 \x03(\x0b\x32\x1a.distributed_chat.LogEntry\x12\x0f\n\x07success\x18\x06 \x01(\x08\x32\x93\x06\n\x0b\x43hatService\x12I\n\x08Register\x12!.distributed_chat.UserCredentials\x1a\x1a.distributed_chat.Response\x12K\n\x05Login\x12!.distributed_chat.UserCredentials\x1a\x1f.distributed_chat.LoginResponse\x12@\n\x06Logout\x12\x1a.distributed_chat.Username\x1a\x1a.distributed_chat.Response\x12G\n\rDeleteAccount\x12\x1a.distributed_chat.Username\x1a\x1a.distributed_chat.Response\x12[\n\x0cListAccounts\x12$.distributed_chat.AccountListRequest\x1a%.distributed_chat.AccountListResponse\x12\x44\n\x0bSendMessage\x12\x19.distributed_chat.Message\x1a\x1a.distributed_chat.Response\x12N\n\x0bGetMessages\x12 .distributed_chat.MessageRequest\x1a\x1d.distributed_chat.MessageList\x12T\n\x0e\x44\x65leteMessages\x12&.distributed_chat.DeleteMessageRequest\x1a\x1a.distributed_chat.Response\x12M\n\nMarkAsRead\x12#.distributed_chat.MarkAsReadRequest\x1a\x1a.distributed_chat.Response\x12I\n\x0eStreamMessages\x12\x1a.distributed_chat.Username\x1a\x19.distributed_chat.Message0\x01\x32\xdf\x02\n\x12ReplicationService\x12L\n\x0bRequestVote\x12\x1d.distributed_chat.VoteRequest\x1a\x1e.distributed_chat.VoteResponse\x12`\n\rAppendEntries\x12&.distributed_chat.AppendEntriesRequest\x1a\'.distributed_chat.AppendEntriesResponse\x12I\n\x08SyncData\x12\x1d.distributed_chat.SyncRequest\x1a\x1e.distributed_chat.SyncResponse\x12N\n\x08GetState\x12!.distributed_chat.GetStateRequest\x1a\x1f.distributed_chat.StateResponseb\x06proto3')

_globals = globals()
_builder.BuildMessageAndEnumDescriptors(DESCRIPTOR, _globals)
_builder.BuildTopDescriptorsAndMessages(DESCRIPTOR, 'distributed_chat.distributed_chat_pb2', _globals)
if not _descriptor._USE_C_DESCRIPTORS:
  DESCRIPTOR._loaded_options = None
  _globals['_USERCREDENTIALS']._serialized_start=61
  _globals['_USERCREDENTIALS']._serialized_end=114
  _globals['_USERNAME']._serialized_start=116
  _globals['_USERNAME']._serialized_end=144
  _globals['_RESPONSE']._serialized_start=146
  _globals['_RESPONSE']._serialized_end=190
  _globals['_LOGINRESPONSE']._serialized_start=192
  _globals['_LOGINRESPONSE']._serialized_end=263
  _globals['_ACCOUNT']._serialized_start=265
  _globals['_ACCOUNT']._serialized_end=332
  _globals['_ACCOUNTLISTREQUEST']._serialized_start=334
  _globals['_ACCOUNTLISTREQUEST']._serialized_end=403
  _globals['_ACCOUNTLISTRESPONSE']._serialized_start=405
  _globals['_ACCOUNTLISTRESPONSE']._serialized_end=503
  _globals['_MESSAGE']._serialized_start=505
  _globals['_MESSAGE']._serialized_end=611
  _globals['_MESSAGEREQUEST']._serialized_start=613
  _globals['_MESSAGEREQUEST']._serialized_end=662
  _globals['_MESSAGELIST']._serialized_start=664
  _globals['_MESSAGELIST']._serialized_end=722
  _globals['_DELETEMESSAGEREQUEST']._serialized_start=724
  _globals['_DELETEMESSAGEREQUEST']._serialized_end=785
  _globals['_MARKASREADREQUEST']._serialized_start=787
  _globals['_MARKASREADREQUEST']._serialized_end=845
  _globals['_VOTEREQUEST']._serialized_start=847
  _globals['_VOTEREQUEST']._serialized_end=943
  _globals['_VOTERESPONSE']._serialized_start=945
  _globals['_VOTERESPONSE']._serialized_end=995
  _globals['_LOGENTRY']._serialized_start=997
  _globals['_LOGENTRY']._serialized_end=1072
  _globals['_APPENDENTRIESREQUEST']._serialized_start=1075
  _globals['_APPENDENTRIESREQUEST']._serialized_end=1245
  _globals['_APPENDENTRIESRESPONSE']._serialized_start=1247
  _globals['_APPENDENTRIESRESPONSE']._serialized_end=1322
  _globals['_SYNCREQUEST']._serialized_start=1324
  _globals['_SYNCREQUEST']._serialized_end=1375
  _globals['_SYNCRESPONSE']._serialized_start=1377
  _globals['_SYNCRESPONSE']._serialized_end=1453
  _globals['_GETSTATEREQUEST']._serialized_start=1455
  _globals['_GETSTATEREQUEST']._serialized_end=1525
  _globals['_STATERESPONSE']._serialized_start=1528
  _globals['_STATERESPONSE']._serialized_end=1694
  _globals['_CHATSERVICE']._serialized_start=1697
  _globals['_CHATSERVICE']._serialized_end=2484
  _globals['_REPLICATIONSERVICE']._serialized_start=2487
  _globals['_REPLICATIONSERVICE']._serialized_end=2838
# @@protoc_insertion_point(module_scope)
