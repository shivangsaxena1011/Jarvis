"""
SHIVANI Skill Validator
Validates skill manifests, semantic versions, entrypoints, and package integrity.
"""

from pathlib import Path
import re
from typing import Any, Dict, List, Optional, Tuple, Union
from pydantic import BaseModel, Field

from skills.manifest import SkillManifest


class ValidationErrorDetail(BaseModel):
    field: str
    message: str


class PackageValidationResult(BaseModel):
    is_valid: bool
    errors: List[ValidationErrorDetail] = Field(default_factory=list)
    manifest: Optional[SkillManifest] = None


class SkillValidator:
    """Strict validator for skill manifests and package structures."""

    NAME_REGEX = re.compile(r"^[a-z0-9][a-z0-9_\-]{2,40}$")
    SEMVER_REGEX = re.compile(r"^(0|[1-9]\d*)\.(0|[1-9]\d*)\.(0|[1-9]\d*)(?:-((?:0|[1-9]\d*|\d*[a-zA-Z-][0-9a-zA-Z-]*)(?:\.(?:0|[1-9]\d*|\d*[a-zA-Z-][0-9a-zA-Z-]*))*))?(?:\+([0-9a-zA-Z-]+(?:\.[0-9a-zA-Z-]+)*))?$")
    PERMISSION_REGEX = re.compile(r"^[a-z0-9_\-]+(?:\.[a-z0-9_\-]+)+$")

    @classmethod
    def validate_manifest(cls, manifest_data: Dict[str, Any]) -> Tuple[bool, List[str], Optional[SkillManifest]]:
        """Validates raw dictionary into SkillManifest, returning (is_valid, errors, manifest)."""
        errors: List[str] = []

        try:
            manifest = SkillManifest(**manifest_data)
        except Exception as e:
            return False, [f"Manifest schema validation error: {e}"], None

        # Validate name slug
        if not cls.NAME_REGEX.match(manifest.name):
            errors.append(f"Invalid skill name '{manifest.name}'. Must be 3-40 lowercase alphanumeric characters with hyphens/underscores.")

        # Validate semver
        if not cls.SEMVER_REGEX.match(manifest.version):
            errors.append(f"Invalid semantic version '{manifest.version}'. Must adhere to semver format (e.g. '1.0.0').")

        # Validate permissions format
        for perm in manifest.permissions:
            if not cls.PERMISSION_REGEX.match(perm):
                errors.append(f"Invalid permission format '{perm}'. Must be in 'scope.action' format (e.g. 'github.read').")

        # Validate entrypoint
        if not manifest.entrypoint.module and not manifest.entrypoint.file:
            errors.append("Skill entrypoint must specify 'module' or 'file'.")
        if not manifest.entrypoint.class_name:
            errors.append("Skill entrypoint must specify 'class_name'.")

        is_valid = len(errors) == 0
        return is_valid, errors, manifest if is_valid else None

    @classmethod
    def validate_package(cls, dir_path: Union[str, Path]) -> PackageValidationResult:
        """Validates an unpacked skill directory and returns PackageValidationResult."""
        p = Path(dir_path).resolve()
        errors: List[ValidationErrorDetail] = []
        if not p.is_dir():
            errors.append(ValidationErrorDetail(field="directory", message=f"Package directory not found: {dir_path}"))
            return PackageValidationResult(is_valid=False, errors=errors)

        manifest = SkillManifest.load_from_directory(p)
        if not manifest:
            errors.append(ValidationErrorDetail(field="manifest", message=f"No valid manifest found in {dir_path}"))
            return PackageValidationResult(is_valid=False, errors=errors)

        is_valid, err_strs, valid_m = cls.validate_manifest(manifest.model_dump())
        for err in err_strs:
            errors.append(ValidationErrorDetail(field="manifest", message=err))

        # Check entrypoint file exists
        entry_file = manifest.entrypoint.entry_file
        file_candidates = [p / entry_file, p / f"{manifest.entrypoint.module}.py", p / manifest.entrypoint.module / "__init__.py"]
        if not any(f.is_file() for f in file_candidates):
            errors.append(ValidationErrorDetail(field="entrypoint", message=f"Entrypoint file '{entry_file}' not found in package directory."))

        return PackageValidationResult(is_valid=(len(errors) == 0), errors=errors, manifest=valid_m if len(errors) == 0 else None)

    @classmethod
    def validate_package_directory(cls, dir_path: str) -> Tuple[bool, List[str], Optional[SkillManifest]]:
        """Backwards compatibility alias returning tuple."""
        res = cls.validate_package(dir_path)
        err_msgs = [f"{e.field}: {e.message}" for e in res.errors]
        return res.is_valid, err_msgs, res.manifest
