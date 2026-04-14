from rest_framework import serializers
from .models import ViewHistory
from .models import SearchHistory
from .models import RecommendationCache
from .models import InteractionEvent, KnowledgeNode, KnowledgeEdge, BehaviorModelSnapshot, RAGDocument

class ViewHistorySerializer(serializers.ModelSerializer):
    class Meta:
        model = ViewHistory
        fields = '__all__'

class SearchHistorySerializer(serializers.ModelSerializer):
    class Meta:
        model = SearchHistory
        fields = '__all__'

class RecommendationCacheSerializer(serializers.ModelSerializer):
    class Meta:
        model = RecommendationCache
        fields = '__all__'


class InteractionEventSerializer(serializers.ModelSerializer):
    class Meta:
        model = InteractionEvent
        fields = '__all__'


class KnowledgeNodeSerializer(serializers.ModelSerializer):
    class Meta:
        model = KnowledgeNode
        fields = '__all__'


class KnowledgeEdgeSerializer(serializers.ModelSerializer):
    source_label = serializers.SerializerMethodField()
    target_label = serializers.SerializerMethodField()

    class Meta:
        model = KnowledgeEdge
        fields = '__all__'

    def get_source_label(self, obj):
        return str(obj.source)

    def get_target_label(self, obj):
        return str(obj.target)


class BehaviorModelSnapshotSerializer(serializers.ModelSerializer):
    class Meta:
        model = BehaviorModelSnapshot
        fields = '__all__'


class RAGDocumentSerializer(serializers.ModelSerializer):
    class Meta:
        model = RAGDocument
        fields = '__all__'


class BuildGraphSerializer(serializers.Serializer):
    customer_id = serializers.IntegerField(required=False)
    full_rebuild = serializers.BooleanField(default=False)


class TrainBehaviorSerializer(serializers.Serializer):
    model_type = serializers.ChoiceField(
        choices=['markov', 'gru4rec', 'transformer', 'gnn'],
        default='markov',
    )
    min_transitions = serializers.IntegerField(default=1, min_value=1)
    epochs = serializers.IntegerField(default=3, min_value=1, max_value=200)


class RetrainScheduleSerializer(serializers.Serializer):
    models = serializers.ListField(
        child=serializers.ChoiceField(choices=['markov', 'gru4rec', 'transformer', 'gnn']),
        required=False,
        default=['gru4rec', 'transformer', 'gnn'],
    )
    min_transitions = serializers.IntegerField(default=1, min_value=1)
    epochs = serializers.IntegerField(default=3, min_value=1, max_value=200)


class RecommendRequestSerializer(serializers.Serializer):
    customer_id = serializers.IntegerField()
    limit = serializers.IntegerField(required=False, default=10, min_value=1, max_value=100)


class ChatRequestSerializer(serializers.Serializer):
    customer_id = serializers.IntegerField(required=False)
    message = serializers.CharField(max_length=2000)
    top_k = serializers.IntegerField(required=False, default=5, min_value=1, max_value=20)

