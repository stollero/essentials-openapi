import pytest

from openapidocs.mk.v3 import OpenAPIV3DocumentationHandler, style_from_value
from tests.common import get_file_json, get_resource_file_content


@pytest.mark.parametrize("example_file", ["example1", "example2", "example3"])
def test_v3_markdown_gen(example_file):
    data = get_file_json(f"{example_file}-openapi.json")
    expected_result = get_resource_file_content(f"{example_file}-output.md")

    handler = OpenAPIV3DocumentationHandler(data)

    html = handler.write(data)

    assert html == expected_result


@pytest.mark.parametrize(
    "input,expected_result",
    [
        (
            {
                "text/plain": {"schema": {"$ref": "#/components/schemas/Release"}},
                "application/json": {
                    "schema": {"$ref": "#/components/schemas/Release"}
                },
                "text/json": {"schema": {"$ref": "#/components/schemas/Release"}},
            },
            {
                "application/json": {
                    "schema": {"$ref": "#/components/schemas/Release"},
                    "alt_types": ["text/json", "text/plain"],
                }
            },
        ),
        (
            {
                "text/xml": {"schema": {"$ref": "#/components/schemas/Release"}},
                "application/xml": {"schema": {"$ref": "#/components/schemas/Release"}},
                "xml": {"schema": {"$ref": "#/components/schemas/Release"}},
                "application/json": {
                    "schema": {"$ref": "#/components/schemas/Release"}
                },
            },
            {
                "application/json": {
                    "schema": {"$ref": "#/components/schemas/Release"}
                },
                "application/xml": {
                    "schema": {"$ref": "#/components/schemas/Release"},
                    "alt_types": ["text/xml", "xml"],
                },
            },
        ),
    ],
)
def test_v3_simplify_content(input, expected_result):
    handler = OpenAPIV3DocumentationHandler({})

    result = handler.simplify_content(input)
    assert result == expected_result


def test_get_empty_schemas():
    handler = OpenAPIV3DocumentationHandler({})

    assert list(handler.get_schemas()) == []


def test_get_properties_missing_data():
    handler = OpenAPIV3DocumentationHandler({})

    properties = handler.get_properties({"$ref": "#/components/schemas/Foo"})
    assert properties == []


def test_expand_references_ref():
    handler = OpenAPIV3DocumentationHandler(
        {
            "components": {
                "schemas": {
                    "Foo": {
                        "type": "object",
                        "properties": {
                            "id": {"type": "string", "format": "uuid"},
                            "ufo": {"$ref": "#/components/schemas/Ufo"},
                        },
                    },
                    "Ufo": {
                        "type": "object",
                        "properties": {
                            "id": {"type": "string", "format": "uuid"},
                            "name": {"type": "string"},
                        },
                    },
                }
            }
        }
    )

    exp = handler.expand_references({"$ref": "#/components/schemas/Foo"})
    assert exp == {
        "type": "object",
        "properties": {
            "id": {"type": "string", "format": "uuid"},
            "ufo": {
                "type": "object",
                "properties": {
                    "id": {"type": "string", "format": "uuid"},
                    "name": {"type": "string"},
                },
            },
        },
    }


def test_generate_example_from_schema_empty():
    handler = OpenAPIV3DocumentationHandler({})

    assert handler.generate_example_from_schema({}) is None


def test_write_content_schema_empty():
    handler = OpenAPIV3DocumentationHandler({})

    assert handler.write_content_schema({}) == ""


def test_get_content_examples():
    handler = OpenAPIV3DocumentationHandler({})

    examples = list(
        handler.get_content_examples(
            {
                "examples": {
                    "one": "Lorem ipsum",
                    "two": {"value": {"a": 1, "b": 2, "c": 3}},
                }
            }
        )
    )

    assert examples[0].value == "Lorem ipsum"
    assert examples[1].value == {"a": 1, "b": 2, "c": 3}


def test_get_parameters_for_security_default():
    handler = OpenAPIV3DocumentationHandler({})

    assert handler.get_parameter_for_security("Foo", {"type": "foo"}) == {
        "name": "Foo",
        "in": "header",
        "description": "",
        "schema": {
            "type": "string",
            "default": "N/A",
            "nullable": False,
        },
    }


def test_iter_bindings():
    handler = OpenAPIV3DocumentationHandler(get_file_json("example1-openapi.json"))

    values = list(handler.iter_schemas_bindings())

    assert values == [
        ("Category", "Release"),
        ("CreateOrganizationsBoundInput", "OrganizationBoundInput"),
        ("ProfessionalContext", "ProfessionalMembership"),
        ("Release", "Category"),
        ("Release", "ReleaseCountry"),
        ("Release", "ReleaseHistory"),
        ("Release", "ReleaseNode"),
        ("Release", "ReleaseOrganization"),
        ("ReleaseCountry", "Country"),
        ("ReleaseCountry", "Release"),
        ("ReleaseHistory", "Release"),
        ("ReleaseNode", "NodeInfo"),
        ("ReleaseNode", "Release"),
        ("ReleaseNodeDownload", "NodeInfo"),
        ("ReleaseNodeDownload", "Release"),
        ("ReleaseNodeDownloadPaginatedSet", "ReleaseNodeDownload"),
        ("ReleaseOrganization", "Release"),
        ("ReleasePaginatedSet", "Release"),
    ]


def test_iter_bindings_arrays():
    handler = OpenAPIV3DocumentationHandler(
        {
            "components": {
                "schemas": {
                    "Pet": {
                        "type": "object",
                        "required": ["id", "name"],
                        "properties": {
                            "id": {"type": "integer", "format": "int64"},
                            "name": {"type": "string"},
                            "tag": {"type": "string"},
                            "category": {
                                "type": "string",
                                "enum": ["One", "Two", "Three"],
                            },
                        },
                    },
                    "Pets": {
                        "type": "array",
                        "items": {"$ref": "#/components/schemas/Pet"},
                    },
                }
            }
        }
    )

    values = list(handler.iter_schemas_bindings())

    assert values == [("Pets", "Pet")]


def test_style_from_value_raises_value_error():
    with pytest.raises(ValueError):
        style_from_value("WRONG")


def test_v3_markdown_gen_handles_missing_components():
    data = {
        "openapi": "3.0.0",
        "info": {
            "version": "1.0.0",
            "title": "Example",
        },
        "paths": {
            "/foo": {
                "get": {
                    "responses": {
                        "200": {
                            "description": "Foo",
                            "content": {"text/plain": {"schema": {"type": "string"}}},
                        },
                    },
                },
            },
        },
    }
    handler = OpenAPIV3DocumentationHandler(data)

    html = handler.write(data)
    with open("___a.html", encoding="utf8", mode="wt") as f:
        f.write(html)
    assert html is not None