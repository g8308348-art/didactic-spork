import os
import xml.etree.ElementTree as ET
from datetime import datetime
from typing import Dict, List


class XMLTemplateProcessor:
    def __init__(self, template_path: str, output_dir: str = None):
        """
        Initialize with the path to the XML template file and output directory.

        Args:
            template_path: Path to the XML template file
            output_dir: Directory to save generated files (default: 'test_data/timestamp')
        """
        self.template_path = template_path
        if output_dir:
            self.output_dir = output_dir
        else:
            self.output_dir = os.path.join(
                "test_data", datetime.now().strftime("%Y%m%d_%H%M%S")
            )
        os.makedirs(self.output_dir, exist_ok=True)

    def generate_test_files(
        self, test_name: str, placeholders: Dict[str, List[str]]
    ) -> List[str]:
        """
        Generate test files based on placeholders.

        Args:
            test_name: Name of the test (e.g., 'screening_response')
            placeholders: Dictionary of placeholder names to lists of values

        Returns:
            List of paths to generated files
        """
        generated_files = []

        if test_name == "Screening response":
            actions = ["stp-release", "release", "block", "reject"]
            for action in actions:
                timestamp_now = datetime.now()
                formatted_upi = f"{timestamp_now.strftime('%Y%m%d%H%M%S')}-{action}"
                filename = f"screening_response_{action}.xml"
                output_path = os.path.join(self.output_dir, filename)
                replacements = {
                    "upi_timestamp": formatted_upi,
                    "timestamp": timestamp_now.isoformat(),
                }
                self._generate_file(replacements, output_path)
                generated_files.append(output_path)

        elif test_name == "Cuban Filter":
            filename = "cuban_filter.xml"
            output_path = os.path.join(self.output_dir, filename)
            self._generate_file({"timestamp": datetime.now().isoformat()}, output_path)
            generated_files.append(output_path)

        return generated_files

    def _generate_file(self, replacements: Dict[str, str], output_path: str) -> None:
        """Generate a single XML file with replacements."""
        try:
            tree = ET.parse(self.template_path)
            root = tree.getroot()

            def replace_in_element(element):
                if element.text and "{" in element.text and "}" in element.text:
                    for key, value in replacements.items():
                        placeholder = f"{{{key}}}"
                        if placeholder in element.text:
                            element.text = element.text.replace(placeholder, value)
                for child in element:
                    replace_in_element(child)

            replace_in_element(root)
            tree.write(output_path, encoding="utf-8", xml_declaration=True)

        except Exception as e:
            print(f"Error generating file {output_path}: {str(e)}")


if __name__ == "__main__":
    processor = XMLTemplateProcessor("template.xml")
    print("Generating screening response test files...")
    files = processor.generate_test_files("Screening response", {})
    print(f"Generated files: {files}")

    print("\nGenerating Cuban Filter test files...")
    files = processor.generate_test_files("Cuban Filter", {})
    print(f"Generated files: {files}")
