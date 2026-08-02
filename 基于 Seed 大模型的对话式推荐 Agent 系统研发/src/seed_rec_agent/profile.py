from __future__ import annotations

import math
import time

from .models import Behavior, FeedbackType, Intent, UserProfile


EVENT_WEIGHT = {
    FeedbackType.LIKE: 1.0,
    FeedbackType.CLICK: 0.45,
    FeedbackType.EXPOSE: 0.0,
    FeedbackType.SKIP: -0.25,
    FeedbackType.DISLIKE: -1.0,
}


class ProfileUpdater:
    def apply_intent(self, profile: UserProfile, intent: Intent) -> None:
        if intent.reset:
            profile.interests.clear()
            profile.disliked_tags.clear()
            profile.preferred_styles.clear()
        for tag in intent.positive_tags:
            profile.interests[tag] = min(3.0, profile.interests.get(tag, 0.0) + 1.2)
            profile.disliked_tags.pop(tag, None)
        for tag in intent.negative_tags:
            # Repeated dislikes become progressively stronger but remain bounded.
            profile.disliked_tags[tag] = min(5.0, profile.disliked_tags.get(tag, 0.0) * 1.35 + 1.0)
            profile.interests.pop(tag, None)
        if intent.styles:
            profile.preferred_styles = set(intent.styles)
        profile.turn_count += 1

    def apply_feedback(self, profile: UserProfile, behavior: Behavior) -> None:
        profile.history.append(behavior)
        age_days = max(0.0, (time.time() - behavior.timestamp) / 86400)
        decay = math.exp(-age_days / 30.0)
        weight = EVENT_WEIGHT[behavior.event] * decay
        if behavior.event == FeedbackType.CLICK:
            weight *= min(1.5, 0.5 + behavior.dwell_seconds / 30.0)
        for tag in behavior.tags:
            if weight >= 0:
                profile.interests[tag] = max(-3.0, min(3.0, profile.interests.get(tag, 0.0) + weight))
            else:
                profile.disliked_tags[tag] = min(5.0, profile.disliked_tags.get(tag, 0.0) + abs(weight))

