from django.contrib import admin
from .models import (
	ActiveModelState,
	BehaviorModelSnapshot,
	InteractionEvent,
	KnowledgeEdge,
	KnowledgeNode,
	RAGDocument,
	RecommendationCache,
	SearchHistory,
	ViewHistory,
)

admin.site.register(ViewHistory)
admin.site.register(SearchHistory)
admin.site.register(RecommendationCache)
admin.site.register(InteractionEvent)
admin.site.register(KnowledgeNode)
admin.site.register(KnowledgeEdge)
admin.site.register(BehaviorModelSnapshot)
admin.site.register(ActiveModelState)
admin.site.register(RAGDocument)
