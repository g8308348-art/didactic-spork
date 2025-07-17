import os
import logging
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional
import xml.etree.ElementTree as ET

# Configure basic logging
logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s"
)


class XMLTemplateProcessor:
    """
    Processes an XML template by replacing placeholders and generates output files.

    Example:
        processor = XMLTemplateProcessor(template_path="template.xml")
        files = processor.generate_test_files(
            test_name="Screening Response"
        )
    """

    def __init__(self, template_path: str, output_dir: Optional[str] = None) -> None:
        """
        Initialize the processor with a template file and an optional output directory.

        Args:
            template_path: Path to the XML template file.
            output_dir: Directory to save generated files. If not provided,
                        a timestamped folder under 'test_data' is created.
        """
        self.template_path = Path(template_path)
        if output_dir:
            self.output_dir = Path(output_dir)
        else:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            self.output_dir = Path("public") / "generated" / timestamp

        self.output_dir.mkdir(parents=True, exist_ok=True)
        logging.info("Output directory: %s", self.output_dir)

    def generate_test_files(self, test_name: str, extra_placeholders: Optional[Dict[str,str]] = None) -> List[str]:
        """
        Generate XML test files based on the specified test name.

        Args:
            test_name: Identifier for the type of test (case-insensitive).
            _placeholders: Currently unused placeholder mapping.

        Returns:
            A list of generated file paths as strings.

        Raises:
            ValueError: If the test_name is not supported.
        """
        generated_files: List[str] = []
        extra_placeholders = extra_placeholders or {}
        key = test_name.strip().lower()

        if key == "screening response":
            actions = ["stp-release", "release", "block", "reject"]
            for action in actions:
                now = datetime.now()
                upi = f"{now.strftime('%Y%m%d%H%M%S')}-{action}"
                filename = f"screening_response_{action}.xml"
                output_path = self.output_dir / filename

                replacements = {"upi_timestamp": upi, "timestamp": now.isoformat()}
                replacements.update(extra_placeholders)
                self._generate_file(replacements, output_path)
                generated_files.append(str(output_path))

        elif key == "cuban filter":
            actions = ["stp-release", "release", "block", "reject"]
            for action in actions:
                now = datetime.now()
                upi = f"{now.strftime('%Y%m%d%H%M%S')}-{action}"
                filename = f"cuban_filter_{action}.xml"
                output_path = self.output_dir / filename

                replacements = {"upi_timestamp": upi, "timestamp": now.isoformat()}
                replacements.update(extra_placeholders)
                self._generate_file(replacements, output_path)
                generated_files.append(str(output_path))

        else:
            msg = f"Unsupported test_name: '{test_name}'"
            logging.error(msg)
            raise ValueError(msg)

        logging.info("Generated files: %s", generated_files)
        return generated_files

    def _generate_file(self, replacements: Dict[str, str], output_path: Path) -> None:
        """
        Create a new XML file by applying replacements to the template.

        Args:
            replacements: Mapping of placeholder keys to replacement text.
            output_path: Destination file path for the generated XML.
        """
        try:
            tree = ET.parse(self.template_path)
            root = tree.getroot()

            # Recursively replace placeholders in element text
            def _replace(node: ET.Element) -> None:
                if node.text:
                    for key, val in replacements.items():
                        placeholder = f"{{{key}}}"
                        if placeholder in node.text:
                            node.text = node.text.replace(placeholder, val)
                for child in node:
                    _replace(child)

            _replace(root)
            tree.write(output_path, encoding="utf-8", xml_declaration=True)
            logging.info("File written: %s", output_path)
        except ET.ParseError as pe:
            logging.error("XML parse error for %s: %s", self.template_path, pe)
            raise
        except Exception as e:
            logging.error("Error generating file %s: %s", output_path, e)
            raise


if __name__ == "__main__":
    processor = XMLTemplateProcessor("template.xml")
    print("Generating screening response test files...")
    files = processor.generate_test_files("Screening Response")
    print(f"Generated files: {files}")

    print("\nGenerating Cuban Filter test files...")
    files = processor.generate_test_files("Cuban Filter")
    print(f"Generated files: {files}")
