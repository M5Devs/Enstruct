import logging
import os
import shutil
import time
from typing import Optional, List

from enstruct.tools.batch import BatchProcessor

logger = logging.getLogger("enstruct.tools.watch")
if not logger.handlers:
    handler = logging.StreamHandler()
    formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
    handler.setFormatter(formatter)
    logger.addHandler(handler)
    logger.setLevel(logging.INFO)


class FolderWatcher:
    """Utility to continuously or periodically scan an inbox folder,

    process audio/video files using BatchProcessor, write outputs to an outbox,

    and move/archive processed input files.

    """



    def __init__(

        self,

        input_dir: str,

        output_dir: str,

        format: str = "srt",

        archive_dir: Optional[str] = None,

        language: Optional[str] = None,

        model_size: str = "large-v3-turbo",

        poll_interval: float = 5.0

    ) -> None:

        """Initializes the FolderWatcher.



        Args:

            input_dir: Directory to scan for new audio/video files.

            output_dir: Directory where subtitles/transcripts will be written.

            format: Output subtitle format ("srt", "vtt", "txt").

            archive_dir: Directory to move processed input files. If None, defaults to input_dir/.processed.

            language: Optional ISO language code.

            model_size: Model size for EnstructTranscriber.

            poll_interval: Seconds to sleep between folder polling iterations.

        """

        self.input_dir = os.path.abspath(input_dir)

        self.output_dir = os.path.abspath(output_dir)

        self.format = format

        self.archive_dir = os.path.abspath(archive_dir) if archive_dir else os.path.join(self.input_dir, ".processed")

        self.language = language

        self.poll_interval = poll_interval



        from enstruct.core.transcriber import EnstructTranscriber

        transcriber = EnstructTranscriber(model_size=model_size)

        self.batch_processor = BatchProcessor(transcriber=transcriber)



    def run_once(self) -> List[str]:

        """Scans the inbox folder once, processes all pending files, and archives them.



        Returns:

            List of processed file names.

        """

        if not os.path.exists(self.input_dir):

            logger.error("Input directory '%s' does not exist.", self.input_dir)

            return []



        os.makedirs(self.output_dir, exist_ok=True)

        os.makedirs(self.archive_dir, exist_ok=True)



        try:

            all_entries = os.listdir(self.input_dir)

        except Exception as e:

            logger.error("Failed to list input directory '%s': %s", self.input_dir, str(e))

            return []



        supported_files = [

            f for f in all_entries

            if os.path.isfile(os.path.join(self.input_dir, f)) and

            os.path.splitext(f.lower())[1] in BatchProcessor.SUPPORTED_EXTENSIONS

        ]



        if not supported_files:

            return []



        logger.info("Found %d file(s) in watch inbox: %s", len(supported_files), supported_files)

        processed = []



        for filename in supported_files:

            input_file_path = os.path.join(self.input_dir, filename)

            try:

                logger.info("Watch folder processing: %s", filename)

                result = self.batch_processor.transcriber.transcribe(input_file_path, language=self.language)



                base_name, _ = os.path.splitext(filename)

                output_file_name = f"{base_name}.{self.format.lower()}"

                output_file_path = os.path.join(self.output_dir, output_file_name)



                self.batch_processor.subtitle_generator.generate(

                    segments=result["segments"],

                    output_path=output_file_path,

                    format=self.format

                )



                # Move processed file to archive directory

                archive_target_path = os.path.join(self.archive_dir, filename)

                shutil.move(input_file_path, archive_target_path)

                logger.info("Processed '%s' -> output saved to '%s' and archived to '%s'", filename, output_file_path, archive_target_path)

                processed.append(filename)



            except Exception as e:

                logger.error("Error processing file '%s' in watch folder: %s", filename, str(e))



        return processed



    def start_watching(self, run_loop: bool = True) -> None:

        """Starts continuous folder watching loop.



        Args:

            run_loop: If True, loops continuously until interrupted.

        """

        logger.info("Starting Watch Folder monitor on '%s' (Output: '%s', Poll: %.1fs)", self.input_dir, self.output_dir, self.poll_interval)

        try:
            while True:
                self.run_once()
                if not run_loop:
                    break
                time.sleep(self.poll_interval)
        except KeyboardInterrupt:
            logger.info("Watch Folder monitor stopped by user.")
