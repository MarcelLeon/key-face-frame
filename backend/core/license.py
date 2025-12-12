"""
License Verification System

Simple local license validation for commercial version.
No network calls, file-based validation only.
"""

import logging
import re
from pathlib import Path
from typing import Dict, Optional

logger = logging.getLogger(__name__)

# License key format: KEY-XXXX-XXXX-XXXX (alphanumeric)
LICENSE_KEY_PATTERN = re.compile(r"^KEY-[A-Z0-9]{4}-[A-Z0-9]{4}-[A-Z0-9]{4}$")

# Default license file path (project root)
DEFAULT_LICENSE_FILE = Path(__file__).parent.parent.parent / "license.key"


class LicenseStatus:
    """License status constants."""

    VALID = "valid"
    INVALID = "invalid"
    MISSING = "missing"
    OPENSOURCE = "opensource"


class LicenseValidator:
    """License validation handler."""

    def __init__(self, license_file: Optional[Path] = None):
        """
        Initialize license validator.

        Args:
            license_file: Path to license file (default: project_root/license.key)
        """
        self.license_file = license_file or DEFAULT_LICENSE_FILE
        self._cached_status: Optional[Dict[str, str]] = None

    def validate(self) -> Dict[str, str]:
        """
        Validate license key.

        Returns:
            Dict with license information:
            {
                "status": "valid" | "invalid" | "missing" | "opensource",
                "message": "Human-readable message",
                "key": "KEY-XXXX-XXXX-XXXX" (if valid, masked as KEY-XXXX-****-****)
            }
        """
        # Return cached status if available
        if self._cached_status:
            return self._cached_status

        # Check if license file exists
        if not self.license_file.exists():
            logger.info("No license.key file found - running in open-source mode")
            self._cached_status = {
                "status": LicenseStatus.OPENSOURCE,
                "message": "开源版本 (Open Source Edition)",
            }
            return self._cached_status

        # Read license key
        try:
            with open(self.license_file, "r", encoding="utf-8") as f:
                license_key = f.read().strip()
        except Exception as e:
            logger.error(f"Failed to read license file: {e}")
            self._cached_status = {
                "status": LicenseStatus.INVALID,
                "message": f"许可证文件读取失败: {str(e)}",
            }
            return self._cached_status

        # Validate format
        if not LICENSE_KEY_PATTERN.match(license_key):
            logger.warning(f"Invalid license key format: {license_key}")
            self._cached_status = {
                "status": LicenseStatus.INVALID,
                "message": "许可证格式无效 (Invalid license format)",
                "help": "请从 Gumroad 获取有效的许可证密钥",
                "purchase_url": "https://gumroad.com/your-product",  # TODO: Update with real URL
            }
            return self._cached_status

        # Valid license
        logger.info(f"Valid license key detected: {self._mask_key(license_key)}")
        self._cached_status = {
            "status": LicenseStatus.VALID,
            "message": "商业版本 (Commercial Edition)",
            "key": self._mask_key(license_key),
        }
        return self._cached_status

    @staticmethod
    def _mask_key(key: str) -> str:
        """
        Mask license key for display (show only first segment).

        Args:
            key: Full license key (KEY-XXXX-XXXX-XXXX)

        Returns:
            Masked key (KEY-XXXX-****-****)
        """
        parts = key.split("-")
        if len(parts) == 4:
            return f"{parts[0]}-{parts[1]}-****-****"
        return "****-****-****-****"

    def is_valid(self) -> bool:
        """
        Check if license is valid.

        Returns:
            True if license is valid, False otherwise
        """
        status = self.validate()
        return status["status"] == LicenseStatus.VALID

    def is_commercial(self) -> bool:
        """
        Check if running commercial version.

        Returns:
            True if commercial (valid license), False if open-source
        """
        status = self.validate()
        return status["status"] == LicenseStatus.VALID

    def clear_cache(self) -> None:
        """Clear cached license status (force re-validation)."""
        self._cached_status = None


# Global license validator instance
license_validator = LicenseValidator()
