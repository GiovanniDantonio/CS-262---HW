# server/raft_service_impl.py
from proto import chat_pb2, chat_pb2_grpc

class MyRaftService(chat_pb2_grpc.RaftServiceServicer):
    def GetClusterStatus(self, request, context):
        # Construct a valid response based on your Raft node state.
        # This is just a dummy example.
        response = chat_pb2.ClusterStatusResponse(
            leader_id="server1",      # Replace with actual leader ID
            current_term=1,           # Replace with actual term
            members=[]                # Fill with actual member data if available
        )
        return response

    def RequestVote(self, request, context):
        context.set_code(context.Code.UNIMPLEMENTED)
        context.set_details("Method not implemented!")
        raise NotImplementedError("Method not implemented!")

    def AppendEntries(self, request, context):
        context.set_code(context.Code.UNIMPLEMENTED)
        context.set_details("Method not implemented!")
        raise NotImplementedError("Method not implemented!")

    def JoinCluster(self, request, context):
        context.set_code(context.Code.UNIMPLEMENTED)
        context.set_details("Method not implemented!")
        raise NotImplementedError("Method not implemented!")

    def TransferSnapshot(self, request, context):
        context.set_code(context.Code.UNIMPLEMENTED)
        context.set_details("Method not implemented!")
        raise NotImplementedError("Method not implemented!")
