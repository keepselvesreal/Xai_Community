"""User reaction repository for data access layer."""

from typing import List, Optional
from beanie import PydanticObjectId
from nadle_backend.models.core import UserReaction
from nadle_backend.exceptions.user import UserNotFoundError


class UserReactionRepository:
    """Repository for user reaction data access operations."""
    
    async def find_by_user(self, user_id: str) -> List[UserReaction]:
        """Find all reactions by user ID.
        
        Args:
            user_id: User ID
            
        Returns:
            List of user reactions
        """
        try:
            reactions = await UserReaction.find({"user_id": user_id}).sort("-created_at").to_list()
            return reactions
        except Exception:
            return []
    
    async def find_by_target(self, target_type: str, target_id: str) -> List[UserReaction]:
        """Find all reactions for a specific target.
        
        Args:
            target_type: Type of target (post or comment)
            target_id: Target ID
            
        Returns:
            List of user reactions for the target
        """
        try:
            reactions = await UserReaction.find({
                "target_type": target_type,
                "target_id": target_id
            }).sort("-created_at").to_list()
            return reactions
        except Exception:
            return []
    
    async def find_user_reaction(self, user_id: str, target_type: str, target_id: str) -> Optional[UserReaction]:
        """Find specific user reaction for a target.
        
        Args:
            user_id: User ID
            target_type: Type of target (post or comment)
            target_id: Target ID
            
        Returns:
            User reaction if found, None otherwise
        """
        try:
            reaction = await UserReaction.find_one({
                "user_id": user_id,
                "target_type": target_type,
                "target_id": target_id
            })
            return reaction
        except Exception:
            return None
    
    async def get_by_id(self, reaction_id: str) -> UserReaction:
        """Get user reaction by ID.
        
        Args:
            reaction_id: Reaction ID
            
        Returns:
            User reaction instance
            
        Raises:
            UserNotFoundError: If reaction not found
        """
        try:
            reaction = await UserReaction.get(PydanticObjectId(reaction_id))
            if not reaction:
                raise UserNotFoundError(user_id=reaction_id)
            return reaction
        except Exception as e:
            raise UserNotFoundError(user_id=reaction_id) from e
    
    async def create(self, user_reaction: UserReaction) -> UserReaction:
        """Create a new user reaction.
        
        Args:
            user_reaction: User reaction instance
            
        Returns:
            Created user reaction
        """
        await user_reaction.save()
        return user_reaction
    
    async def update(self, user_reaction: UserReaction) -> UserReaction:
        """Update user reaction.
        
        Args:
            user_reaction: User reaction instance
            
        Returns:
            Updated user reaction
        """
        await user_reaction.save()
        return user_reaction
    
    async def delete(self, reaction_id: str) -> bool:
        """Delete user reaction.
        
        Args:
            reaction_id: Reaction ID
            
        Returns:
            True if successful
        """
        try:
            reaction = await self.get_by_id(reaction_id)
            await reaction.delete()
            return True
        except Exception:
            return False
    
    async def count_reactions_by_type(self, target_type: str, target_id: str) -> dict:
        """Count reactions by type for a target.
        
        Args:
            target_type: Type of target (post or comment)
            target_id: Target ID
            
        Returns:
            Dictionary with reaction counts
        """
        try:
            like_count = await UserReaction.find({
                "target_type": target_type,
                "target_id": target_id,
                "liked": True
            }).count()
            
            dislike_count = await UserReaction.find({
                "target_type": target_type,
                "target_id": target_id,
                "disliked": True
            }).count()
            
            bookmark_count = await UserReaction.find({
                "target_type": target_type,
                "target_id": target_id,
                "bookmarked": True
            }).count()
            
            return {
                "like_count": like_count,
                "dislike_count": dislike_count,
                "bookmark_count": bookmark_count
            }
        except Exception:
            return {
                "like_count": 0,
                "dislike_count": 0,
                "bookmark_count": 0
            }