<!--
Letta API Reference Documentation
Copyright (C) 2025 Mark Hopkins
Licensed under CC-BY-SA 4.0
-->

# Letta Notes

### Python SDK

<Note>
The legacy Letta Python `LocalClient`/`RestClient` SDK is available under `pip install letta` (which also contains the server).
This client is deprecated and will be replaced in a future release with the new `letta-client`.
Please migrate any Python code using the old `RESTClient` or `LocalClient` to use `letta-client` to avoid breaking changes in the future.
</Note>

The Letta [Python SDK](https://github.com/letta-ai/letta-python) can be downloaded with:
```bash
pip install letta-client
```

Once installed, you can instantiate the client in your Python code with:
```python
from letta_client import Letta

# connect to a local server
client = Letta(base_url="http://localhost:8283")

# connect to Letta Cloud
client = Letta(token="LETTA_API_KEY")
```

(( our server is not localhost. We'll be connecting to a VPS server.

https://your-letta-server.com:8283
pw YOUR_PASSWORD <- configure this in your environment

We'll want to configure this in the admin dashboard settings.

))

### Development Notes

#### Identity Management
- Identities must be explicitly specified as "user" type when creating them
- User context is not automatically maintained between messages - each message must include the identity_id
- Core memory blocks should be attached to user identities to maintain context
- When sending messages, always include the identity_id parameter to maintain conversation context

Example identity creation:
```python
# Create a user identity
identity = {
    "identifier_key": "user_123",
    "name": "John Doe",
    "identity_type": "user"  # Important: must specify as "user"
}
```

Example message with identity:
```python
client.agents.messages.create(
    agent_id="agent_id",
    messages=[MessageCreate(role="user", content="Hello")],
    identity_id="user_123"  # Include identity_id to maintain context
)
```

#### Core Block Management
- Each user identity should have an associated core memory block named `Persona_<username>`
- The core block should be created when the identity is created
- The core block should be attached to the identity as a variable
- Message flow:
  1. Create the block using `client.blocks.create()`
  2. Attach the user's `Persona_<username>` core block to the agent
  3. Send the message with the user's identity_id
  4. Detach the user's core block from the agent
- This ensures the agent has access to the user's persona information during the conversation
- Core blocks should contain relevant user information, preferences, and conversation history

#### CRITICAL: Block ID Management
- The `client.blocks.list()` operation is currently unreliable and may not show all blocks
- This is a known issue being investigated by the core team
- **DESIGN REQUIREMENT**: All block IDs must be cached locally
- Block IDs should be stored in the database alongside user records
- Never rely on `client.blocks.list()` for block discovery or management

Implementation Details:
```python
# Create a new block
block = client.blocks.create(
    label=f"Persona_{username}",
    value={
        "name": username,
        "preferences": {},
        "conversation_history": []
    }
)

# Store block ID in database
user_record.block_id = block.id
user_record.save()

# Core block operations (using cached block ID)
client.blocks.retrieve(block_id=user_record.block_id)
client.blocks.modify(block_id=user_record.block_id, value=new_content)
client.agents.blocks.attach(agent_id=agent_id, block_id=user_record.block_id)
client.agents.blocks.detach(agent_id=agent_id, block_id=user_record.block_id)

# NEVER use list() for block discovery
# client.blocks.list()  # DO NOT USE - unreliable
```

Example Usage:
```python
# Create and manage a user's persona block
block_label = f"Persona_{username}"
block_content = {
    "name": username,
    "preferences": {},
    "conversation_history": []
}

# Create the block first
block = client.blocks.create(
    label=block_label,
    value=block_content
)

# Store block ID in database
user_record.block_id = block.id
user_record.save()

# Attach block before sending message
client.agents.blocks.attach(agent_id=agent_id, block_id=user_record.block_id)
try:
    # Send message with identity
    response = client.agents.messages.create(
        agent_id=agent_id,
        messages=[MessageCreate(role="user", content=message)],
        identity_id=identity_id
    )
finally:
    # Always detach block after message
    client.agents.blocks.detach(agent_id=agent_id, block_id=user_record.block_id)
```

---

Below here: SDK references.
Health:
from letta_client import Letta

client = Letta(
    token="YOUR_TOKEN",
)
client.health.check()

List Identities:
curl http://localhost:8283/v1/identities/ \
     -H "Authorization: Bearer <token>"

Create Identities:
curl -X POST http://localhost:8283/v1/identities/ \
     -H "Authorization: Bearer <token>" \
     -H "Content-Type: application/json" \
     -d '{
  "identifier_key": "identifier_key",
  "name": "name",
  "identity_type": "org"
}'

Upsert Identities:
curl -X PUT http://localhost:8283/v1/identities/ \
     -H "Authorization: Bearer <token>" \
     -H "Content-Type: application/json" \
     -d '{
  "identifier_key": "identifier_key",
  "name": "name",
  "identity_type": "org"
}'

Retrieve Identity
curl http://localhost:8283/v1/identities/identity_id \
     -H "Authorization: Bearer <token>"

Delete Identity
curl -X DELETE http://localhost:8283/v1/identities/identity_id \
     -H "Authorization: Bearer <token>"

Modify Identity
curl -X PATCH http://localhost:8283/v1/identities/identity_id \
     -H "Authorization: Bearer <token>" \
     -H "Content-Type: application/json" \
     -d '{}'

List Agents:
from letta_client import Letta

client = Letta(
    token="YOUR_TOKEN",
)
client.agents.list()

Retrieve Agent Context: 
from letta_client import Letta

client = Letta(
    token="YOUR_TOKEN",
)
client.agents.context.retrieve(
    agent_id="agent_id",
)

List Messages:
from letta_client import Letta

client = Letta(
    token="YOUR_TOKEN",
)
client.agents.messages.list(
    agent_id="agent_id",
)

Send Messages:
from letta_client import Letta, MessageCreate

client = Letta(
    token="YOUR_TOKEN",
)
client.agents.messages.create(
    agent_id="agent_id",
    messages=[
      MessageCreate(
        role="user",
        content="content",
      )
    ],
)

Modify Message:
from letta_client import Letta

client = Letta(
    token="YOUR_TOKEN",
)
client.agents.messages.modify(
    agent_id="agent_id",
    message_id="message_id",
)

Send Message Streaming:
from letta_client import Letta, MessageCreate

client = Letta(
    token="YOUR_TOKEN",
)
response = client.agents.messages.create_stream(
    agent_id="agent_id",
    messages=[
      MessageCreate(
        role="user",
        content="content",
      )
    ],
)
for chunk in response:
  yield chunk


  Send message async:

  from letta_client import Letta, MessageCreate

client = Letta(
    token="YOUR_TOKEN",
)
client.agents.messages.create_async(
    agent_id="agent_id",
    messages=[
      MessageCreate(
        role="user",
        content="content",
      )
    ],
)

IDENTITY STUFF: We'll use this to attach to Person records in the DB - it keeps the different conversations and memory blocks seperate.

For some reason it doesn't seem to be (yet) supported by the SDK, so we'll need to write our own library for managing identity.

List Identities:
curl http://localhost:8283/v1/identities/ \
     -H "Authorization: Bearer <token>"

Create Identity
curl -X POST http://localhost:8283/v1/identities/ \
     -H "Authorization: Bearer <token>" \
     -H "Content-Type: application/json" \
     -d '{
  "identifier_key": "identifier_key",
  "name": "name",
  "identity_type": "org"
}'

Upsert Identity
curl -X PUT http://localhost:8283/v1/identities/ \
     -H "Authorization: Bearer <token>" \
     -H "Content-Type: application/json" \
     -d '{
  "identifier_key": "identifier_key",
  "name": "name",
  "identity_type": "org"
}'

Retrieve Identity:
curl http://localhost:8283/v1/identities/identity_id \
     -H "Authorization: Bearer <token>"

Delete Identity:
curl -X DELETE http://localhost:8283/v1/identities/identity_id \
     -H "Authorization: Bearer <token>"

Modify Identity:
curl -X PATCH http://localhost:8283/v1/identities/identity_id \
     -H "Authorization: Bearer <token>" \
     -H "Content-Type: application/json" \
     -d '{}'


---

Retrieve Block:
from letta_client import Letta

client = Letta(
    token="YOUR_TOKEN",
)
client.agents.blocks.retrieve(
    agent_id="agent_id",
    block_label="block_label",
)

Modify Block:
from letta_client import Letta

client = Letta(
    token="YOUR_TOKEN",
)
client.agents.blocks.modify(
    agent_id="agent_id",
    block_label="block_label",
)

List Blocks:
from letta_client import Letta

client = Letta(
    token="YOUR_TOKEN",
)
client.agents.blocks.list(
    agent_id="agent_id",
)

Attach Block:
from letta_client import Letta

client = Letta(
    token="YOUR_TOKEN",
)
client.agents.blocks.attach(
    agent_id="agent_id",
    block_id="block_id",
)

Detach Block:
from letta_client import Letta

client = Letta(
    token="YOUR_TOKEN",
)
client.agents.blocks.detach(
    agent_id="agent_id",
    block_id="block_id",
)

Create Block
from letta_client import Letta

client = Letta(
    token="YOUR_TOKEN",
)
client.blocks.create(
    value="value",
    label="label",
)


NOTE - List Blocks MAY not list all blocks. Seems buggy. Core team is looking into it.

---

## Archival Memory / Passages API

Archival memory (also called passages) provides long-term storage for agent memories. Unlike core memory blocks which are always loaded, archival memory is searched semantically when needed.

### List Passages (Archival Memory)
Retrieve the memories in an agent's archival memory store (paginated query).

**Endpoint:** `GET /v1/agents/:agent_id/archival-memory`

```python
from letta_client import Letta

client = Letta(
    token="YOUR_TOKEN",
)
client.agents.passages.list(
    agent_id="agent_id",
    after=None,           # Unique ID of the memory to start the query range at
    before=None,          # Unique ID of the memory to end the query range at
    limit=None,           # How many results to include in the response
    search=None,          # Search passages by text
    ascending=True        # Sort oldest to newest (True, default) or newest to oldest (False)
)
```

**Response:** Returns a list of passage objects with fields including:
- `text` - The text of the passage
- `embedding` - The embedding of the passage (optional)
- `id` - The passage ID (format: "passage-xxxxxxxx")
- `created_at` - Creation timestamp
- `updated_at` - Last update timestamp
- `tags` - Tags associated with this passage
- `archive_id` - The archive containing this passage
- `source_id` - The data source of the passage
- `file_id` - Associated file ID (if any)
- `metadata` - Additional metadata

### Create Passage
Insert a memory into an agent's archival memory store.

**Endpoint:** `POST /v1/agents/:agent_id/archival-memory`

```python
from letta_client import Letta

client = Letta(
    token="YOUR_TOKEN",
)
client.agents.passages.create(
    agent_id="agent_id",
    text="Text to write to archival memory",
    tags=["tag1", "tag2"],           # Optional list of tags
    created_at="2024-01-15T09:30:00Z"  # Optional timestamp (defaults to current UTC time)
)
```

**Response:** Returns the created passage object with all fields populated.

### Search Archival Memory
Search archival memory using semantic (embedding-based) search with optional temporal filtering.

This endpoint allows manual triggering of archival memory searches, enabling users to query an agent's archival memory store directly via the API. The search uses the same functionality as the agent's `archival_memory_search` tool but is accessible for external API usage.

**Endpoint:** `POST /v1/agents/:agent_id/archival-memory/search`

```python
from letta_client import Letta

client = Letta(
    token="YOUR_TOKEN",
)
client.agents.passages.search(
    agent_id="agent_id",
    query="search query text",
    tags=["tag1"],        # Optional: filter by tags
    match="any"           # How to match tags: 'any' or 'all'
)
```

**Response:** Returns search results with:
- `results` - List of matching passages with `timestamp`, `content`, and `tags`
- `count` - Total number of results

### Delete Passage
Delete a passage from an agent's archival memory.

**Endpoint:** `DELETE /v1/agents/:agent_id/archival-memory/:memory_id`

```python
from letta_client import Letta

client = Letta(
    token="YOUR_TOKEN",
)
client.agents.passages.delete(
    agent_id="agent_id",
    memory_id="passage-xxxxxxxx"
)
```

### Modify Passage
Modify an existing passage in archival memory.

**Endpoint:** `PATCH /v1/agents/:agent_id/archival-memory/:memory_id`

```python
from letta_client import Letta

client = Letta(
    token="YOUR_TOKEN",
)
client.agents.passages.modify(
    agent_id="agent_id",
    memory_id="passage-xxxxxxxx",
    text="Updated text",           # Optional: update the text
    tags=["new_tag"]              # Optional: update tags
)
```

### Usage Notes
- Passages are automatically embedded when created
- Semantic search uses embeddings to find relevant memories
- Passages can be tagged for better organization and filtering
- The archival memory store is separate from core memory blocks
- Archival memories are retrieved on-demand rather than always loaded