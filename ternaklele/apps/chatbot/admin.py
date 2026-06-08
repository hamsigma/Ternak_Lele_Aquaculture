from django.contrib import admin
from .models import ChatSession, ChatMessage
from .vector_models import KnowledgeVector


class ChatMessageInline(admin.TabularInline):
    model = ChatMessage
    extra = 0
    readonly_fields = ["sender_type", "message_text", "created_at"]
    can_delete = False


@admin.register(ChatSession)
class ChatSessionAdmin(admin.ModelAdmin):
    list_display = ["id", "user", "context_summary", "created_at", "updated_at"]
    search_fields = ["user__username", "context_summary"]
    inlines = [ChatMessageInline]
    readonly_fields = ["created_at", "updated_at"]


@admin.register(KnowledgeVector)
class KnowledgeVectorAdmin(admin.ModelAdmin):
    list_display = ["id", "source_type", "source_id", "content_preview", "created_at"]
    list_filter = ["source_type"]
    readonly_fields = ["embedding", "created_at"]

    def content_preview(self, obj):
        return obj.content[:80]
    content_preview.short_description = "Konten"
