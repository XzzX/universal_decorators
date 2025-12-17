import hashlib
import inspect
from typing import Annotated, Any, get_args, get_origin

from pydantic import BaseModel


class Annotation(BaseModel):
    label: str | None = None
    datatype: type | None = None
    unit: str | None = None
    quantity: str | None = None


class PythonImport(BaseModel):
    module: str
    qualname: str
    version: str | None = None


class Metadata(BaseModel):
    author_name: str
    author_email: str

    python_import: PythonImport

    source_code: str
    source_code_hash: str

    docstring: str
    inputs: dict[str, Annotation | None]
    outputs: dict[str, Annotation | None]


def _parse_annotation(annotation) -> Annotation:
    if annotation is None:
        return Annotation()

    origin = get_origin(annotation)
    if origin is not Annotated:
        return Annotation(datatype=annotation)

    args = get_args(annotation)
    annotation = Annotation()
    if isinstance(args[1], dict):
        annotation.model_validate(args[1])
    annotation.datatype = args[0]
    return annotation


def _parse_arguments(sig: inspect.Signature) -> dict[str, Annotation | None]:
    arguments = {}
    for param_name, param in sig.parameters.items():
        arguments[param_name] = (
            _parse_annotation(param.annotation)
            if param.annotation != inspect.Parameter.empty
            else None
        )
    return arguments


def _parse_and_unpack_annotation(annotation) -> dict[str, Annotation | None]:
    origin = get_origin(annotation)
    args = get_args(annotation)

    # unpack one level of Annotated
    if origin is Annotated:
        origin = get_origin(args[0])
        args = get_args(args[0])

    if origin is tuple:
        annotations = {}
        args = get_args(annotation)
        for i, arg in enumerate(args):
            ann = _parse_annotation(arg)
            annotations[ann.label if ann.label is not None else str(i)] = ann
        return annotations

    return {
        "output": _parse_annotation(annotation)
        if annotation != inspect.Signature.empty
        else None
    }


def parse(obj: Any, author_name: str, author_email: str) -> Metadata | None:
    if not (inspect.isfunction(obj) or inspect.ismethod(obj)):
        return None

    source_code = inspect.getsource(obj)
    source_code_hash = hashlib.sha256(source_code.encode()).hexdigest()

    sig = inspect.signature(obj)
    inputs = _parse_arguments(sig)

    return_annotation = sig.return_annotation
    outputs = _parse_and_unpack_annotation(return_annotation)

    return Metadata(
        author_name=author_name,
        author_email=author_email,
        python_import=PythonImport(
            module=obj.__module__
            if hasattr(obj, "__module__")
            else obj.__class__.__module__,
            qualname=obj.__qualname__
            if hasattr(obj, "__qualname__")
            else str(obj.__class__.__qualname__),
        ),
        source_code=source_code,
        source_code_hash=source_code_hash,
        docstring=inspect.getdoc(obj) or "",
        inputs=inputs,
        outputs=outputs,
    )
