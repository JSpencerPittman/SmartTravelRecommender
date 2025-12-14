from django.contrib import admin
from chat.models import ConversationModel
from chat.cqrs.queries import QueryRetrieveMessages
from accounts.models import AccountModel
from django.shortcuts import render  # type: ignore
from django.urls import path  # type: ignore
from dataclasses import dataclass


@dataclass
class UsageStatisics(object):
    num_accounts: int
    num_conversations: int
    num_calls: int
    num_tokens: int

    @property
    def calls_per_user(self):
        return self.num_calls / self.num_accounts

    @property
    def conversations_per_user(self):
        return self.num_conversations / self.num_accounts

    @property
    def tokens_per_call(self):
        return self.num_tokens / self.num_calls

    @classmethod
    def calculate(cls):
        num_accounts = AccountModel.objects.count()
        num_conversations = ConversationModel.objects.count()
        num_calls = 0
        num_tokens = 0

        for conversation in ConversationModel.objects.all():
            messages = QueryRetrieveMessages.execute(conversation.id)["data"]
            tokens_per_response = [
                len(msg.message.split(" ")) for msg in messages if msg.is_user
            ]
            num_calls += len(tokens_per_response)
            num_tokens += sum(tokens_per_response)

        return cls(num_accounts, num_conversations, num_calls, num_tokens)

    def to_dict(self) -> dict[str, float]:
        return {
            "num_accounts": self.num_accounts,
            "num_conversations": self.num_conversations,
            "num_calls": self.num_calls,
            "conversations_per_user": self.conversations_per_user,
            "calls_per_user": self.calls_per_user,
            "tokens_per_call": self.tokens_per_call,
        }


def usage_statistics_page(request):
    stats = UsageStatisics.calculate()
    return render(request, "usage.html", stats.to_dict())


original_get_urls = admin.site.get_urls


def get_admin_urls():
    custom_urls = [
        path(
            "usage-statistics",
            admin.site.admin_view(usage_statistics_page),
            name="usage_statistics",
        )
    ]
    return custom_urls + original_get_urls()


admin.site.get_urls = get_admin_urls

admin.site.register(ConversationModel)
