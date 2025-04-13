import os
from typing import AsyncGenerator, Annotated
from fastapi.middleware.cors import CORSMiddleware

from fastapi import Depends, FastAPI, HTTPException, status
import uvicorn

from pymongo import AsyncMongoClient
from pymongo.asynchronous.collection import AsyncCollection
from models import (
    Article,
    ArticleMongoModel,
    Comment,
    CommentMongoModel,
    CommentMutationResponse,
    NewArticleDto,
    ArticleMutationResponse,
    NewCommentDto,
    NewReplyDto,
    Reply,
    ReplyMongoModel,
    ReplyMutationResponse,
    article_mongo_model_to_article,
    comment_mongo_model_to_comment,
    reply_mongo_model_to_reply,
)

app = FastAPI()

# CORS for all origins
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


async def get_client() -> AsyncGenerator[AsyncMongoClient, None]:
    async with AsyncMongoClient(os.getenv("MONGO_URI")) as client:
        yield client


@app.post("/{platform}/articles", status_code=status.HTTP_201_CREATED)
async def create_article(
    platform: str,
    client: Annotated[AsyncMongoClient, Depends(get_client)],
    payload: NewArticleDto,
) -> ArticleMutationResponse:
    database = client[platform]
    collection: AsyncCollection[ArticleMongoModel] = database["articles"]

    await collection.create_index("article_id", unique=True)
    await collection.create_index("url", unique=True)

    # check if the article already exists
    if await collection.find_one({"article_id": payload.id}):
        return ArticleMutationResponse(success=True, exists=True)

    await collection.insert_one(
        {
            "article_id": payload.id,
            "url": payload.url,
            "title": payload.title,
            "created_at": payload.created_at,
            "content": payload.content,
        }
    )

    return ArticleMutationResponse(success=True, exists=False)


@app.post(
    "/{platform}/articles/{article_id}/comments", status_code=status.HTTP_201_CREATED
)
async def create_comment(
    platform: str,
    article_id: str,
    client: Annotated[AsyncMongoClient, Depends(get_client)],
    payload: NewCommentDto,
) -> CommentMutationResponse:
    database = client[platform]

    article_collection: AsyncCollection[ArticleMongoModel] = database["articles"]
    collection: AsyncCollection[CommentMongoModel] = database["comments"]

    await collection.create_index(("article_id", "comment_id"), unique=True)

    # find if the article exists
    article = await article_collection.find_one({"article_id": article_id})
    if not article:
        raise HTTPException(status_code=404, detail="Article not found")
    assert "_id" in article

    # check if the comment already exists
    if await collection.find_one(
        {"article_id": article["_id"], "comment_id": payload.id}
    ):
        return CommentMutationResponse(success=True, exists=True)

    await collection.insert_one(
        {
            "article_id": article["_id"],
            "comment_id": payload.id,
            "content": payload.content,
            "created_at": payload.created_at,
            "author": payload.author,
            "likes": payload.likes,
            "mark": payload.mark,
        }
    )

    return CommentMutationResponse(success=True, exists=False)


@app.post(
    "/{platform}/articles/{article_id}/comments/{comment_id}/replies",
    status_code=status.HTTP_201_CREATED,
)
async def create_reply(
    platform: str,
    article_id: str,
    comment_id: str,
    client: Annotated[AsyncMongoClient, Depends(get_client)],
    payload: NewReplyDto,
) -> ReplyMutationResponse:
    database = client[platform]

    article_collection: AsyncCollection[ArticleMongoModel] = database["articles"]
    comment_collection: AsyncCollection[CommentMongoModel] = database["comments"]
    collection: AsyncCollection[ReplyMongoModel] = database["replies"]

    await collection.create_index(("article_id", "comment_id", "reply_id"), unique=True)

    # find if the article exists
    article = await article_collection.find_one({"article_id": article_id})
    if not article:
        raise HTTPException(status_code=404, detail="Article not found")
    assert "_id" in article

    # find if the comment exists
    comment = await comment_collection.find_one(
        {"article_id": article["_id"], "comment_id": comment_id}
    )
    if not comment:
        raise HTTPException(status_code=404, detail="Comment not found")
    assert "_id" in comment

    # check if the reply already exists
    if await collection.find_one(
        {
            "article_id": article["_id"],
            "comment_id": comment["_id"],
            "reply_id": payload.id,
        }
    ):
        return ReplyMutationResponse(success=True, exists=True)

    await collection.insert_one(
        {
            "article_id": article["_id"],
            "comment_id": comment["_id"],
            "reply_id": payload.id,
            "content": payload.content,
            "created_at": payload.created_at,
            "author": payload.author,
            "likes": payload.likes,
        }
    )

    return ReplyMutationResponse(success=True, exists=False)


@app.get("/{platform}/articles/{article_id}/comments/{comment_id}/replies")
async def get_replies(
    platform: str,
    article_id: str,
    comment_id: str,
    client: Annotated[AsyncMongoClient, Depends(get_client)],
) -> list[Reply]:
    database = client[platform]
    collection: AsyncCollection[ReplyMongoModel] = database["replies"]
    article_collection: AsyncCollection[ArticleMongoModel] = database["articles"]
    comment_collection: AsyncCollection[CommentMongoModel] = database["comments"]

    # get article object id
    article = await article_collection.find_one({"article_id": article_id})
    if not article:
        raise HTTPException(status_code=404, detail="Article not found")
    assert "_id" in article

    # get comment object id
    comment = await comment_collection.find_one(
        {"article_id": article["_id"], "comment_id": comment_id}
    )
    if not comment:
        raise HTTPException(status_code=404, detail="Comment not found")
    assert "_id" in comment

    cursor = collection.find({"article_id": article["_id"], "comment_id": comment["_id"]})
    return [reply_mongo_model_to_reply(reply, article_id, comment_id) for reply in await cursor.to_list(None)]


@app.get("/{platform}/articles/{article_id}/comments/{comment_id}")
async def get_comment(
    platform: str,
    article_id: str,
    comment_id: str,
    client: Annotated[AsyncMongoClient, Depends(get_client)],
) -> Comment:
    database = client[platform]
    collection: AsyncCollection[CommentMongoModel] = database["comments"]
    article_collection: AsyncCollection[ArticleMongoModel] = database["articles"]

    # get article object id 
    article = await article_collection.find_one({"article_id": article_id})
    if not article:
        raise HTTPException(status_code=404, detail="Article not found")
    assert "_id" in article

    result = await collection.find_one(
        {"article_id": article["_id"], "comment_id": comment_id}
    )
    if not result:
        raise HTTPException(status_code=404, detail="Comment not found")

    return comment_mongo_model_to_comment(result, article_id)


@app.get("/{platform}/articles/{article_id}/comments")
async def get_comments(
    platform: str,
    article_id: str,
    client: Annotated[AsyncMongoClient, Depends(get_client)],
) -> list[Comment]:
    database = client[platform]
    collection: AsyncCollection[CommentMongoModel] = database["comments"]
    article_collection: AsyncCollection[ArticleMongoModel] = database["articles"]
    # get article object id
    article = await article_collection.find_one({"article_id": article_id})
    if not article:
        raise HTTPException(status_code=404, detail="Article not found")
    assert "_id" in article

    return [
        comment_mongo_model_to_comment(comment, article_id)
        for comment in await collection.find({"article_id": article["_id"]}).to_list(None)
    ]


@app.get("/{platform}/articles/{article_id}")
async def get_article(
    platform: str,
    article_id: str,
    client: Annotated[AsyncMongoClient, Depends(get_client)],
) -> Article:
    database = client[platform]
    collection: AsyncCollection[ArticleMongoModel] = database["articles"]

    result = await collection.find_one({"article_id": article_id})
    if not result:
        raise HTTPException(status_code=404, detail="Article not found")

    return article_mongo_model_to_article(result)


@app.get("/{platform}/articles")
async def get_articles(
    platform: str,
    client: Annotated[AsyncMongoClient, Depends(get_client)],
) -> list[Article]:
    database = client[platform]
    collection: AsyncCollection[ArticleMongoModel] = database["articles"]

    return [
        article_mongo_model_to_article(article)
        for article in await collection.find({}).to_list(None)
    ]


if __name__ == "__main__":
    port = int(os.environ.get("PORT", "8080"))

    uvicorn.run(app, host="0.0.0.0", port=port)
