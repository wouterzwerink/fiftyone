# import eta.core.utils as etau

# from fiftyone.core.fields import (
#     Field,
#     BooleanField,
#     ClassesField,
#     DateTimeField,
#     DictField,
#     EmbeddedDocumentField,
#     EmbeddedDocumentListField,
#     IntField,
#     ListField,
#     ObjectIdField,
#     StringField,
#     TargetsField,
# )


# class SerializableDocument(object):
#     """Mixin for documents that can be serialized in BSON or JSON format."""

#     def __str__(self):
#         return self.__repr__()

#     def __repr__(self):
#         return self.fancy_repr()

#     def __eq__(self, other):
#         if not isinstance(other, self.__class__):
#             return False

#         return self.to_dict() == other.to_dict()

#     def fancy_repr(
#         self,
#         class_name=None,
#         select_fields=None,
#         exclude_fields=None,
#         **kwargs
#     ):
#         """Generates a customizable string representation of the document.

#         Args:
#             class_name (None): optional class name to use
#             select_fields (None): iterable of field names to restrict to
#             exclude_fields (None): iterable of field names to exclude
#             **kwargs: additional key-value pairs to include in the string
#                 representation

#         Returns:
#             a string representation of the document
#         """
#         d = {}
#         for f in self._get_repr_fields():
#             if (select_fields is not None and f not in select_fields) or (
#                 exclude_fields is not None and f in exclude_fields
#             ):
#                 continue

#             if not f.startswith("_"):
#                 value = getattr(self, f)
#                 if isinstance(value, ObjectId):
#                     d[f] = str(value)
#                 else:
#                     d[f] = value

#         d.update(kwargs)

#         doc_name = class_name or self.__class__.__name__
#         doc_str = fou.pformat(d)
#         return "<%s: %s>" % (doc_name, doc_str)

#     def has_field(self, field_name):
#         """Determines whether the document has a field of the given name.

#         Args:
#             field_name: the field name

#         Returns:
#             True/False
#         """
#         raise NotImplementedError("Subclass must implement `has_field()`")

#     def get_field(self, field_name):
#         """Gets the field of the document.

#         Args:
#             field_name: the field name

#         Returns:
#             the field value

#         Raises:
#             AttributeError: if the field does not exist
#         """
#         raise NotImplementedError("Subclass must implement `get_field()`")

#     def set_field(self, field_name, value, create=False):
#         """Sets the value of a field of the document.

#         Args:
#             field_name: the field name
#             value: the field value
#             create (False): whether to create the field if it does not exist

#         Raises:
#             ValueError: if ``field_name`` is not an allowed field name or does
#                 not exist and ``create == False``
#         """
#         raise NotImplementedError("Subclass must implement `set_field()`")

#     def clear_field(self, field_name):
#         """Clears the field from the document.

#         Args:
#             field_name: the field name

#         Raises:
#             ValueError: if the field does not exist
#         """
#         raise NotImplementedError("Subclass must implement `clear_field()`")

#     def _get_field_names(self, include_private=False):
#         """Returns an ordered tuple of field names of this document.

#         Args:
#             include_private (False): whether to include private fields

#         Returns:
#             a tuple of field names
#         """
#         raise NotImplementedError("Subclass must implement `_get_field_names`")

#     def _get_repr_fields(self):
#         """Returns an ordered tuple of field names that should be included in
#         the ``repr`` of the document.

#         Returns:
#             a tuple of field names
#         """
#         raise NotImplementedError("Subclass must implement `_get_repr_fields`")

#     def copy(self):
#         """Returns a deep copy of the document.

#         Returns:
#             a :class:`SerializableDocument`
#         """
#         return deepcopy(self)

#     def to_dict(self, extended=False):
#         """Serializes this document to a BSON/JSON dictionary.

#         Args:
#             extended (False): whether to serialize extended JSON constructs
#                 such as ObjectIDs, Binary, etc. into JSON format

#         Returns:
#             a dict
#         """
#         raise NotImplementedError("Subclass must implement `to_dict()`")

#     @classmethod
#     def from_dict(cls, d, extended=False):
#         """Loads the document from a BSON/JSON dictionary.

#         Args:
#             d: a dictionary
#             extended (False): whether the input dictionary may contain
#                 serialized extended JSON constructs

#         Returns:
#             a :class:`SerializableDocument`
#         """
#         raise NotImplementedError("Subclass must implement `from_dict()`")

#     def to_json(self, pretty_print=False):
#         """Serializes the document to a JSON string.

#         Args:
#             pretty_print (False): whether to render the JSON in human readable
#                 format with newlines and indentations

#         Returns:
#             a JSON string
#         """
#         if not pretty_print:
#             return json_util.dumps(self.to_dict())

#         d = self.to_dict(extended=True)
#         return etas.json_to_str(d, pretty_print=pretty_print)

#     @classmethod
#     def from_json(cls, s):
#         """Loads the document from a JSON string.

#         Returns:
#             a :class:`SerializableDocument`
#         """
#         d = json_util.loads(s)
#         return cls.from_dict(d, extended=False)


# class MongoEngineBaseDocument(SerializableDocument):
#     """Mixin for all :class:`mongoengine:mongoengine.base.BaseDocument`
#     subclasses that implements the :class:`SerializableDocument` interface.
#     """

#     def __delattr__(self, name):
#         self.clear_field(name)

#     def __delitem__(self, name):
#         self.clear_field(name)

#     def __deepcopy__(self, memo):
#         # pylint: disable=no-member, unsubscriptable-object
#         kwargs = {
#             f: deepcopy(self.get_field(f), memo)
#             for f in self._fields_ordered
#             if f not in ("_cls", "_id", "id")
#         }
#         return self.__class__(**kwargs)

#     def has_field(self, field_name):
#         # pylint: disable=no-member
#         return field_name in self._fields_ordered

#     def get_field(self, field_name):
#         return getattr(self, field_name)

#     def set_field(self, field_name, value, create=False):
#         if not create and not self.has_field(field_name):
#             raise AttributeError(
#                 "%s has no field '%s'" % (self.__class__.__name__, field_name)
#             )

#         setattr(self, field_name, value)

#     def clear_field(self, field_name):
#         if not self.has_field(field_name):
#             raise AttributeError(
#                 "%s has no field '%s'" % (self.__class__.__name__, field_name)
#             )

#         super().__delattr__(field_name)

#         # pylint: disable=no-member
#         if field_name not in self.__class__._fields_ordered:
#             self._fields_ordered = tuple(
#                 f for f in self._fields_ordered if f != field_name
#             )

#     def field_to_mongo(self, field_name):
#         # pylint: disable=no-member
#         value = self.get_field(field_name)
#         return self._fields[field_name].to_mongo(value)

#     def field_to_python(self, field_name, value):
#         # pylint: disable=no-member
#         return self._fields[field_name].to_python(value)

#     def _get_field_names(self, include_private=False):
#         if not include_private:
#             return tuple(
#                 f for f in self._fields_ordered if not f.startswith("_")
#             )

#         return self._fields_ordered

#     def _get_repr_fields(self):
#         # pylint: disable=no-member
#         return self._fields_ordered

#     def to_dict(self, extended=False):
#         # pylint: disable=no-member
#         d = self.to_mongo(use_db_field=True)

#         if not extended:
#             return d

#         # @todo is there a way to avoid bson -> str -> json dict?
#         return json.loads(json_util.dumps(d))

#     @classmethod
#     def from_dict(cls, d, extended=False):
#         if not extended:
#             try:
#                 # Attempt to load the document directly, assuming it is in
#                 # extended form

#                 # pylint: disable=no-member
#                 return cls._from_son(d)
#             except Exception:
#                 pass

#         # Construct any necessary extended JSON components like ObjectIds
#         # @todo is there a way to avoid json -> str -> bson?
#         d = json_util.loads(json_util.dumps(d))

#         # pylint: disable=no-member
#         return cls._from_son(d)


# class BaseEmbeddedDocument(MongoEngineBaseDocument):
#     """Base class for documents that are embedded within other documents and
#     therefore are not stored in their own collection in the database.
#     """


# class EmbeddedDocument(BaseEmbeddedDocument):
#     """Base class for documents that are embedded within other documents and
#     therefore are not stored in their own collection in the database.
#     """

#     meta = {"abstract": True, "allow_inheritance": True}

#     def __init__(self, *args, **kwargs):
#         super().__init__(*args, **kwargs)
#         self.validate()


# class SampleFieldDocument(EmbeddedDocument):
#     """Description of a sample field."""

#     name = StringField()
#     ftype = StringField()
#     subfield = StringField(null=True)
#     embedded_doc_type = StringField(null=True)
#     db_field = StringField(null=True)
#     fields = ListField(
#         EmbeddedDocumentField(document_type="SampleFieldDocument")
#     )

#     def to_field(self):
#         """Creates the :class:`fiftyone.core.fields.Field` specified by this
#         document.

#         Returns:
#             a :class:`fiftyone.core.fields.Field`
#         """
#         ftype = etau.get_class(self.ftype)

#         embedded_doc_type = self.embedded_doc_type
#         if embedded_doc_type is not None:
#             embedded_doc_type = etau.get_class(embedded_doc_type)

#         subfield = self.subfield
#         if subfield is not None:
#             subfield = etau.get_class(subfield)

#         fields = None
#         if self.fields is not None:
#             fields = [field_doc.to_field() for field_doc in list(self.fields)]

#         return create_field(
#             self.name,
#             ftype,
#             embedded_doc_type=embedded_doc_type,
#             subfield=subfield,
#             db_field=self.db_field,
#             fields=fields,
#         )

#     @classmethod
#     def from_field(cls, field):
#         """Creates a :class:`SampleFieldDocument` for a field.

#         Args:
#             field: a :class:`fiftyone.core.fields.Field` instance

#         Returns:
#             a :class:`SampleFieldDocument`
#         """
#         embedded_doc_type = cls._get_attr_repr(field, "document_type")
#         if isinstance(field, (ListField, DictField)) and field.field:
#             embedded_doc_type = cls._get_attr_repr(
#                 field.field, "document_type"
#             )

#         return cls(
#             name=field.name,
#             ftype=etau.get_class_name(field),
#             subfield=cls._get_attr_repr(field, "field"),
#             embedded_doc_type=embedded_doc_type,
#             db_field=field.db_field,
#             fields=cls._get_field_documents(field),
#         )

#     def matches_field(self, field):
#         """Determines whether this sample field matches the given field.

#         Args:
#             field: a :class:`fiftyone.core.fields.Field` instance

#         Returns:
#             True/False
#         """
#         if self.name != field.name:
#             return False

#         if self.ftype != etau.get_class_name(field):
#             return False

#         if self.subfield and self.subfield != etau.get_class_name(field.field):
#             return False

#         if (
#             self.embedded_doc_type
#             and self.embedded_doc_type
#             != etau.get_class_name(field.document_type)
#         ):
#             return False

#         if self.db_field != field.db_field:
#             return False

#         cur_fields = {f.name: f for f in list(getattr(self, "fields", []))}
#         fields = {f.name: f for f in getattr(field, "fields", [])}
#         if cur_fields and fields:
#             if len(fields) != len(cur_fields):
#                 return False

#             if any([name not in cur_fields for name in fields]):
#                 return False

#             return any(
#                 [not cur_fields[name].matches(fields[name]) for name in fields]
#             )

#         return True

#     def merge_doc(self, other):
#         if self.ftype != other.ftype:
#             raise TypeError("Cannot merge")

#         if other.ftype == etau.get_class_name(ListField):
#             if (
#                 self.subfield
#                 and other.subfield
#                 and self.subfield != other.subfield
#             ):
#                 raise TypeError("Cannot merge")

#             self.subfield = other.subfield or self.subfield

#         if self.name == other.name and self.db_field is None:
#             self.db_field = other.db_field or self.db_field

#         embedded_doc = etau.get_class_name(EmbeddedDocumentField)
#         if other.ftype == embedded_doc or self.subfield == embedded_doc:
#             if (
#                 self.embedded_doc_type
#                 and other.embedded_doc_type
#                 and self.embedded_doc_type != other.embedded_doc_type
#             ):
#                 raise TypeError("Cannot merge")

#             self.embedded_doc_type = (
#                 other.embedded_doc_type or self.embedded_doc_type
#             )

#             others = {f.name: f for f in other.fields}

#             new = []
#             for i, field in enumerate(self.fields):
#                 if field.name in others:
#                     self.fields[i] = field.merge_doc(others[field.name])
#                 else:
#                     new.append(field)

#             self.fields = self.fields + new

#         return self

#     @staticmethod
#     def _get_attr_repr(field, attr_name):
#         attr = getattr(field, attr_name, None)
#         return etau.get_class_name(attr) if attr else None

#     @classmethod
#     def _get_field_documents(cls, field):
#         if isinstance(field, ListField):
#             field = field.field

#         if not isinstance(field, EmbeddedDocumentField):
#             return None

#         if not hasattr(field, "fields"):
#             return None

#         return [
#             cls.from_field(value)
#             for value in field.get_field_schema().values()
#         ]
