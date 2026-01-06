from rest_framework import serializers
from django.utils.timezone import now
from .models import Contest, ContestItem, ContestRegistration, ContestParticipant
from problems.models import Problem


class ContestAddItemSerializer(serializers.Serializer):
    """
    Serializer for adding problem or challenge to contest.
    
    Rules:
    - item_type: 'PROBLEM' or 'CHALLENGE'
    - item_id: ID of the problem or challenge
    - order: Position in contest (1, 2, 3, ...)
    - score: (optional) Contest-specific score override
    """
    item_type = serializers.ChoiceField(choices=['PROBLEM', 'CHALLENGE'])
    item_id = serializers.IntegerField(min_value=1)
    order = serializers.IntegerField(min_value=1)
    score = serializers.IntegerField(default=100, min_value=1)

    def validate_item_type(self, value):
        """Validate item type"""
        if value not in ['PROBLEM', 'CHALLENGE']:
            raise serializers.ValidationError(
                "item_type must be 'PROBLEM' or 'CHALLENGE'"
            )
        return value

    def validate_order(self, value):
        """Order must be positive integer"""
        if value < 1:
            raise serializers.ValidationError("Order must be at least 1")
        return value

    def validate_score(self, value):
        """Score must be positive"""
        if value < 1:
            raise serializers.ValidationError("Score must be at least 1")
        return value


class ContestAddManagerSerializer(serializers.Serializer):
    """Serializer for adding manager to contest"""
    user_id = serializers.IntegerField(min_value=1)

    def validate_user_id(self, value):
        """Verify user exists"""
        from django.contrib.auth import get_user_model
        User = get_user_model()
        
        try:
            User.objects.get(id=value)
        except User.DoesNotExist:
            raise serializers.ValidationError("User not found")
        
        return value


class ContestListSerializer(serializers.ModelSerializer):
    """Minimal contest serializer for list views"""
    created_by = serializers.StringRelatedField()

    class Meta:
        model = Contest
        fields = [
            "id",
            "title",
            "slug",
            "start_time",
            "end_time",
            "is_public",
            "created_by",
        ]


class ContestItemSerializer(serializers.ModelSerializer):
    """Serialize problem or challenge in contest"""
    title = serializers.SerializerMethodField()
    slug = serializers.SerializerMethodField()
    difficulty = serializers.SerializerMethodField()
    item_type = serializers.CharField(source='get_item_type_display_lower')

    class Meta:
        model = ContestItem
        fields = [
            "id",
            "order",
            "item_type",
            "title",
            "slug",
            "difficulty",
            "score"
        ]

    def get_title(self, obj):
        """Get problem or challenge title"""
        return obj.problem.title if obj.problem else obj.challenge.title

    def get_slug(self, obj):
        """Get problem or challenge slug"""
        return obj.problem.slug if obj.problem else obj.challenge.slug

    def get_difficulty(self, obj):
        """Get problem or challenge difficulty"""
        return obj.problem.difficulty if obj.problem else obj.challenge.difficulty


class ContestCreateSerializer(serializers.ModelSerializer):
    """Serializer for creating/updating contests"""
    
    class Meta:
        model = Contest
        fields = [
            "title",
            "slug",
            "description",
            "start_time",
            "end_time",
            "is_public",
            "logo",
            "rules",
        ]

    def validate(self, attrs):
        """Validate contest timing and fields"""
        start_time = attrs.get('start_time')
        end_time = attrs.get('end_time')
        title = attrs.get('title')

        if not title or len(title.strip()) < 3:
            raise serializers.ValidationError({
                'title': 'Title must be at least 3 characters'
            })

        if start_time and end_time:
            if start_time >= end_time:
                raise serializers.ValidationError({
                    'end_time': 'End time must be after start time'
                })
            
            if start_time < now():
                raise serializers.ValidationError({
                    'start_time': 'Start time cannot be in the past'
                })
        
        return attrs


class ContestDetailSerializer(serializers.ModelSerializer):
    """Enhanced detail serializer with state info"""
    created_by = serializers.StringRelatedField()
    managers = serializers.StringRelatedField(many=True)
    contest_items = serializers.SerializerMethodField()
    current_state = serializers.SerializerMethodField()
    can_edit = serializers.SerializerMethodField()
    can_add_items = serializers.SerializerMethodField()
    time_status = serializers.SerializerMethodField()

    class Meta:
        model = Contest
        fields = [
            "id",
            "title",
            "slug",
            "description",
            "rules",
            "logo",
            "start_time",
            "end_time",
            "state",
            "current_state",
            "is_published",
            "created_by",
            "managers",
            "contest_items",
            "can_edit",
            "can_add_items",
            "time_status",
        ]

    def get_contest_items(self, obj):
        """Only return items if contest is LIVE or user is manager"""
        request = self.context.get('request')
        
        if not request:
            return []
        
        is_manager = (
            request.user.is_superuser or
            obj.created_by == request.user or
            request.user in obj.managers.all()
        )

        # Show items only if LIVE or manager
        if obj.state == 'LIVE' or is_manager:
            items = obj.contest_items.all().order_by('order')
            return ContestItemSerializer(items, many=True).data
        return []

    def get_current_state(self, obj):
        """Get computed state based on current time"""
        current_time = now()
        
        if current_time < obj.start_time:
            return "UPCOMING"
        elif current_time < obj.end_time:
            return "ONGOING"
        else:
            return "FINISHED"

    def get_can_edit(self, obj):
        """Only draft/scheduled contests can be edited"""
        request = self.context.get('request')
        
        if not request or not request.user.is_authenticated:
            return False
        
        is_manager = (
            request.user.is_superuser or
            obj.created_by == request.user or
            request.user in obj.managers.all()
        )
        return is_manager and obj.state in ['DRAFT', 'SCHEDULED']

    def get_can_add_items(self, obj):
        """Items can be added only in DRAFT/SCHEDULED"""
        request = self.context.get('request')
        
        if not request or not request.user.is_authenticated:
            return False
        
        is_manager = (
            request.user.is_superuser or
            obj.created_by == request.user or
            request.user in obj.managers.all()
        )
        return is_manager and obj.state in ['DRAFT', 'SCHEDULED']

    def get_time_status(self, obj):
        """Human-readable time status"""
        current_time = now()
        
        if current_time < obj.start_time:
            delta = obj.start_time - current_time
            return {
                "status": "UPCOMING",
                "seconds_until_start": delta.total_seconds()
            }
        elif current_time < obj.end_time:
            delta = obj.end_time - current_time
            return {
                "status": "ONGOING",
                "seconds_until_end": delta.total_seconds()
            }
        else:
            return {
                "status": "FINISHED",
                "ended_at": obj.end_time
            }


class ContestDetailWithRegistrationSerializer(serializers.ModelSerializer):
    """Enhanced detail view with registration info"""
    created_by = serializers.StringRelatedField()
    managers = serializers.StringRelatedField(many=True)
    contest_items = serializers.SerializerMethodField()
    registered_count = serializers.SerializerMethodField()
    is_user_registered = serializers.SerializerMethodField()
    can_register = serializers.SerializerMethodField()
    status = serializers.SerializerMethodField()

    class Meta:
        model = Contest
        fields = [
            "id",
            "title",
            "slug",
            "description",
            "start_time",
            "end_time",
            "created_by",
            "managers",
            "contest_items",
            "is_public",
            "registered_count",
            "is_user_registered",
            "can_register",
            "status",
        ]

    def get_contest_items(self, obj):
        """Show items if LIVE"""
        if obj.state == 'LIVE':
            items = obj.contest_items.all().order_by('order')
            return ContestItemSerializer(items, many=True).data
        return []

    def get_registered_count(self, obj):
        return obj.registrations.filter(
            status__in=['REGISTERED', 'PARTICIPATED']
        ).count()

    def get_is_user_registered(self, obj):
        request = self.context.get('request')
        if request and request.user.is_authenticated:
            return obj.registrations.filter(
                user=request.user,
                status__in=['REGISTERED', 'PARTICIPATED']
            ).exists()
        return False

    def get_can_register(self, obj):
        """User can register if contest hasn't started yet"""
        return now() < obj.start_time

    def get_status(self, obj):
        current_time = now()
        if current_time < obj.start_time:
            return "UPCOMING"
        elif current_time < obj.end_time:
            return "ONGOING"
        else:
            return "ENDED"


class ContestRegistrationSerializer(serializers.ModelSerializer):
    """Serializer for contest registrations"""
    user_username = serializers.CharField(source='user.username', read_only=True)
    user_email = serializers.CharField(source='user.email', read_only=True)

    class Meta:
        model = ContestRegistration
        fields = [
            'id',
            'user',
            'user_username',
            'user_email',
            'status',
            'registered_at',
            'participated_at',
        ]
        read_only_fields = ['id', 'registered_at', 'participated_at']