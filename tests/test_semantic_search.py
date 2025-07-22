import importlib
import os
import sys
import types

import pytest

class DummyModel:
    def encode(self, texts):
        if isinstance(texts, str):
            texts = [texts]
        return [[0.0] * 5 for _ in texts]

def load_semantic_search(monkeypatch):
    # Ensure project root on path
    root = os.path.dirname(os.path.dirname(__file__))
    sys.path.insert(0, root)
    # Stub out heavy dependency
    dummy_module = types.ModuleType('sentence_transformers')
    dummy_module.SentenceTransformer = lambda *args, **kwargs: DummyModel()
    monkeypatch.setitem(sys.modules, 'sentence_transformers', dummy_module)
    if 'semantic_search' in sys.modules:
        del sys.modules['semantic_search']
    module = importlib.import_module('semantic_search')
    return module


def test_preprocess_query_translations(monkeypatch):
    sem = load_semantic_search(monkeypatch)
    engine = sem.AIToolsSemanticSearch.__new__(sem.AIToolsSemanticSearch)
    result = engine.preprocess_query("צ'אט בוט חינמי!!!")
    assert result == 'chat bot free'


def test_get_random_tools_returns_copies(monkeypatch):
    sem = load_semantic_search(monkeypatch)
    engine = sem.AIToolsSemanticSearch.__new__(sem.AIToolsSemanticSearch)
    engine.tools_data = [
        {'name': 'Tool1', 'url': '', 'description': '', 'category': '', 'popularity': '', 'pricing': '', 'tags': ''},
        {'name': 'Tool2', 'url': '', 'description': '', 'category': '', 'popularity': '', 'pricing': '', 'tags': ''},
    ]
    results = engine.get_random_tools(count=2)
    assert len(results) == 2
    for original, ret in zip(engine.tools_data, results):
        assert ret is not original
    results[0]['name'] = 'Changed'
    assert engine.tools_data[0]['name'] == 'Tool1'
