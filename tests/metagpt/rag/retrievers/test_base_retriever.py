from metagpt.rag.retrievers.base import ModifiableRAGRetriever, PersistableRAGRetriever


class SubModifiableRAGRetriever(ModifiableRAGRetriever):
    ...


class SubPersistableRAGRetriever(PersistableRAGRetriever):
    ...


class TestModifiableRAGRetriever:
    def test_subclasshook(self):
        result = SubModifiableRAGRetriever.__subclasshook__(SubModifiableRAGRetriever)
        assert result is NotImplemented


class TestPersistableRAGRetriever:
    def test_subclasshook(self):
        result = SubPersistableRAGRetriever.__subclasshook__(SubPersistableRAGRetriever)
        assert result is NotImplemented
