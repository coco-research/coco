"""ChromaDB worker — reads JSON from stdin, performs upsert, writes JSON to stdout.

Replaces inline f-string code generation in memory_bridge.py.
Usage: echo '{"op":"upsert","items":[...]}' | python3 chroma_worker.py
"""
import json
import sys

def main():
    try:
        data = json.loads(sys.stdin.read())
    except json.JSONDecodeError as e:
        print(json.dumps({"status": "error", "message": f"invalid JSON: {e}"}))
        sys.exit(1)

    op = data.get("op")
    palace_path = data.get("palace_path")
    collection_name = data.get("collection_name")

    if not palace_path or not collection_name:
        print(json.dumps({"status": "error", "message": "missing palace_path or collection_name"}))
        sys.exit(1)

    try:
        import chromadb
        client = chromadb.PersistentClient(path=palace_path)
        col = client.get_collection(collection_name)

        if op == "upsert":
            items = data.get("items", [])
            ids = [item["id"] for item in items]
            documents = [item["text"] for item in items]
            metadatas = [item["metadata"] for item in items]
            col.upsert(ids=ids, documents=documents, metadatas=metadatas)
            print(json.dumps({"status": "ok", "upserted": len(ids)}))

        elif op == "get_ids":
            where = data.get("where", {})
            limit = data.get("limit", 10000)
            results = col.get(where=where, limit=limit)
            print(json.dumps({"status": "ok", "ids": results["ids"]}))

        elif op == "stats":
            project_wing = data.get("project_wing", "")
            total = col.count()
            project_ids = col.get(where={"wing": project_wing}, limit=10000)["ids"] if project_wing else []
            print(json.dumps({"status": "ok", "total": total, "project": len(project_ids)}))

        else:
            print(json.dumps({"status": "error", "message": f"unknown op: {op}"}))
            sys.exit(1)

    except Exception as e:
        print(json.dumps({"status": "error", "message": str(e)[:500]}))
        sys.exit(1)

if __name__ == "__main__":
    main()
