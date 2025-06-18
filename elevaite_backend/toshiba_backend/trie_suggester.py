
class TrieNode:
    def __init__(self):
        self.children = {}
        self.value = None

class AbbreviationTrie:
    def __init__(self):
        self.root = TrieNode()

    def insert(self, key: str, value: str):
        node = self.root
        for char in key:
            if char not in node.children:
                node.children[char] = TrieNode()
            node = node.children[char]
        node.value = value

    def get_all_with_prefix(self, prefix: str):
        def dfs(node, path, results):
            if node.value:
                results.append((''.join(path), node.value))
            for char, next_node in node.children.items():
                dfs(next_node, path + [char], results)

        node = self.root
        for char in prefix:
            if char not in node.children:
                return []
            node = node.children[char]

        results = []
        dfs(node, list(prefix), results)
        return results
