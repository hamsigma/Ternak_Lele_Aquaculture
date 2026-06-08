from rest_framework import generics, permissions, status
from rest_framework.response import Response
from rest_framework.views import APIView

from .models import ChatSession, ChatMessage
from .serializers import ChatSessionSerializer, ChatInputSerializer
from .rag_pipeline import get_ai_response


class ChatView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request):
        serializer = ChatInputSerializer(data=request.data)
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

        user_message = serializer.validated_data["message"]
        session_id = serializer.validated_data.get("session_id")

        # Buat atau ambil sesi yang ada
        if session_id:
            session = ChatSession.objects.filter(id=session_id, user=request.user).first()
            if not session:
                return Response({"detail": "Sesi tidak ditemukan."}, status=status.HTTP_404_NOT_FOUND)
        else:
            session = ChatSession.objects.create(user=request.user)

        # Ambil riwayat percakapan untuk konteks
        history = [
            {"role": msg.sender_type, "content": msg.message_text}
            for msg in session.messages.all()
        ]

        # Simpan pesan user
        ChatMessage.objects.create(
            session=session,
            sender_type=ChatMessage.SenderType.USER,
            message_text=user_message
        )

        # Dapatkan respons AI
        ai_response = get_ai_response(user_message, history)

        # Simpan respons AI
        ChatMessage.objects.create(
            session=session,
            sender_type=ChatMessage.SenderType.AI,
            message_text=ai_response
        )

        # Update context summary
        session.context_summary = user_message[:200]
        session.save(update_fields=["context_summary", "updated_at"])

        return Response({
            "session_id": session.id,
            "response": ai_response,
        })


class ChatSessionListView(generics.ListAPIView):
    serializer_class = ChatSessionSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        return ChatSession.objects.filter(user=self.request.user)


class ChatSessionDetailView(generics.RetrieveDestroyAPIView):
    serializer_class = ChatSessionSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        return ChatSession.objects.filter(user=self.request.user)
