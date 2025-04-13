from datetime import datetime
from typing import Literal, NotRequired, TypedDict
from bson import ObjectId
from pydantic import BaseModel


class NewArticleDto(BaseModel):
    id: str
    title: str
    created_at: datetime
    content: str
    url: str


class ArticleMongoModel(TypedDict):
    _id: NotRequired[ObjectId]
    article_id: str
    url: str
    title: str
    created_at: datetime
    content: str


class Article(BaseModel):
    id: str
    url: str
    title: str
    created_at: datetime
    content: str


def article_mongo_model_to_article(article: ArticleMongoModel) -> Article:
    return Article(
        id=article["article_id"],
        url=article["url"],
        title=article["title"],
        created_at=article["created_at"],
        content=article["content"],
    )


class NewCommentDto(BaseModel):
    id: str
    content: str
    created_at: datetime
    author: str
    likes: int | None = None
    dislikes: int | None = None
    reaction_type: Literal["+1", "-1", "0"] | None = None


class CommentMongoModel(TypedDict):
    _id: NotRequired[ObjectId]
    article_id: ObjectId
    comment_id: str  # index (article_id, comment_id)
    content: str
    created_at: datetime
    author: str
    likes: int | None
    dislikes: int | None
    reaction_type: Literal["+1", "-1", "0"] | None


class Comment(BaseModel):
    id: str
    article_id: str
    content: str
    created_at: datetime
    author: str
    likes: int | None
    dislikes: int | None
    reaction_type: Literal["+1", "-1", "0"] | None


def comment_mongo_model_to_comment(comment: CommentMongoModel, article_id: str) -> Comment:
    return Comment(
        id=comment["comment_id"],
        article_id=article_id,
        content=comment["content"],
        created_at=comment["created_at"],
        author=comment["author"],
        likes=comment["likes"],
        reaction_type=comment["reaction_type"],
        dislikes=comment["dislikes"],
    )


class NewReplyDto(BaseModel):
    id: str
    content: str
    created_at: datetime
    author: str
    likes: int | None = None
    dislikes: int | None = None
    reaction_type: Literal["+1", "-1", "0"] | None = None


class ReplyMongoModel(TypedDict):
    _id: NotRequired[ObjectId]
    article_id: ObjectId
    comment_id: ObjectId
    reply_id: str  # index (article_id, comment_id, reply_id)
    content: str
    created_at: datetime
    author: str
    likes: int | None
    dislikes: int | None
    reaction_type: Literal["+1", "-1", "0"] | None


class Reply(BaseModel):
    id: str
    article_id: str
    comment_id: str
    content: str
    created_at: datetime
    author: str
    likes: int | None
    dislikes: int | None
    reaction_type: Literal["+1", "-1", "0"] | None


def reply_mongo_model_to_reply(reply: ReplyMongoModel, article_id: str, comment_id: str) -> Reply:
    return Reply(
        id=reply["reply_id"],
        article_id=article_id,
        comment_id=comment_id,
        content=reply["content"],
        created_at=reply["created_at"],
        author=reply["author"],
        likes=reply["likes"],
        dislikes=reply["dislikes"],
        reaction_type=reply["reaction_type"],
    )


class ArticleMutationResponse(BaseModel):
    success: bool
    exists: bool


class CommentMutationResponse(BaseModel):
    success: bool
    exists: bool


class ReplyMutationResponse(BaseModel):
    success: bool
    exists: bool
