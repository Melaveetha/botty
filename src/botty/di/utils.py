from typing import Annotated, get_args, get_origin

from .markers import Depends


def _extract_depends(annotation):
    if get_origin(annotation) is Annotated:
        _, *metadata = get_args(annotation)
        for meta in metadata:
            if isinstance(meta, Depends):
                return meta
    return None
