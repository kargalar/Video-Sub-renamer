"""
File matching logic for video-subtitle pairing.
Contains algorithms for similarity scoring and file matching operations.
"""

import os
import re
import difflib


class FileMatcher:
    """Handles file matching logic for videos and subtitles."""

    def __init__(self):
        self.video_files = []
        self.subtitle_files = []
        self.matches = []

    def levenshtein_distance(self, s1, s2):
        """
        Calculate Levenshtein distance between two strings (edit distance).

        Args:
            s1 (str): First string
            s2 (str): Second string

        Returns:
            int: Edit distance between strings
        """
        try:
            if len(s1) < len(s2):
                return self.levenshtein_distance(s2, s1)

            if len(s2) == 0:
                return len(s1)

            previous_row = range(len(s2) + 1)
            for i, c1 in enumerate(s1):
                current_row = [i + 1]
                for j, c2 in enumerate(s2):
                    insertions = previous_row[j + 1] + 1
                    deletions = current_row[j] + 1
                    substitutions = previous_row[j] + (c1 != c2)
                    current_row.append(min(insertions, deletions, substitutions))
                previous_row = current_row

            print(f"Debug: Levenshtein distance between '{s1}' and '{s2}': {previous_row[-1]}")
            return previous_row[-1]
        except Exception as e:
            print(f"Debug: Error calculating Levenshtein distance: {str(e)}")
            return max(len(s1), len(s2))

    def similarity_score(self, str1, str2):
        """
        Calculate advanced similarity score between two strings.

        Args:
            str1 (str): First string
            str2 (str): Second string

        Returns:
            float: Similarity score between 0.0 and 1.0
        """
        try:
            str1 = str1.lower()
            str2 = str2.lower()

            # Exact match check (file names same except extension)
            if str1 == str2:
                return 1.0

            # Extract season and episode information
            # Comprehensive regex patterns: s01e01, 1x01, season 1 episode 1 formats
            season_ep_patterns = [
                r's(\d+)e(\d+)',  # s01e01 format
                r'(\d+)x(\d+)',   # 1x01 format
                r'season\s*(\d+)\s*episode\s*(\d+)',  # season 1 episode 1 format
                r'e(\d+)',        # episode number only (e01)
            ]

            # Extract season and episode numbers from both strings
            str1_season = None
            str1_episode = None
            str2_season = None
            str2_episode = None

            for pattern in season_ep_patterns:
                str1_match = re.search(pattern, str1)
                if str1_match:
                    if len(str1_match.groups()) == 2:
                        str1_season = int(str1_match.group(1))
                        str1_episode = int(str1_match.group(2))
                    else:
                        str1_episode = int(str1_match.group(1))
                    break

            for pattern in season_ep_patterns:
                str2_match = re.search(pattern, str2)
                if str2_match:
                    if len(str2_match.groups()) == 2:
                        str2_season = int(str2_match.group(1))
                        str2_episode = int(str2_match.group(2))
                    else:
                        str2_episode = int(str2_match.group(1))
                    break

            # If both have season and episode info and they match, give highest score
            if (str1_season is not None and str2_season is not None and
                str1_episode is not None and str2_episode is not None):
                if str1_season == str2_season and str1_episode == str2_episode:
                    return 1.0
                # Same season but different episode, low score
                elif str1_season == str2_season:
                    return 0.3
                # Completely different, very low score
                else:
                    return 0.1

            # If only episode numbers match, high score
            elif (str1_episode is not None and str2_episode is not None and
                  str1_episode == str2_episode):
                return 0.8

            # Subset check (one string contained in the other)
            if str1 in str2:
                # Higher score if at beginning or end
                if str2.startswith(str1) or str2.endswith(str1):
                    return 0.9
                # Lower score if in middle
                else:
                    return 0.8
            elif str2 in str1:
                # Higher score if at beginning or end
                if str1.startswith(str2) or str1.endswith(str2):
                    return 0.9
                # Lower score if in middle
                else:
                    return 0.8

            # Word-based similarity
            words1 = set(re.findall(r'\w+', str1))
            words2 = set(re.findall(r'\w+', str2))

            if words1 and words2:
                # Common word ratio
                common_words = words1.intersection(words2)
                word_similarity = len(common_words) / max(len(words1), len(words2))

                # If common word ratio is high
                if word_similarity > 0.7:
                    return 0.7 + (word_similarity * 0.3)  # Between 0.7 and 1.0

            # Difflib sequence similarity
            sequence_similarity = difflib.SequenceMatcher(None, str1, str2).ratio()

            # Levenshtein similarity
            max_len = max(len(str1), len(str2))
            if max_len > 0:
                levenshtein_similarity = 1 - (self.levenshtein_distance(str1, str2) / max_len)
            else:
                levenshtein_similarity = 0

            # Count common characters
            common_chars = sum(1 for c in str1 if c in str2)

            # Calculate basic similarity ratio
            char_similarity = common_chars / max(len(str1), len(str2)) if max(len(str1), len(str2)) > 0 else 0

            # Weighted average of all similarity scores
            final_similarity = (
                sequence_similarity * 0.4 +
                levenshtein_similarity * 0.3 +
                char_similarity * 0.3
            )

            print(f"Debug: Similarity score between '{str1}' and '{str2}': {final_similarity:.3f}")
            return final_similarity

        except Exception as e:
            print(f"Debug: Error calculating similarity score: {str(e)}")
            return 0.0

    def scan_directory(self, folder_path, skip_x_files=False):
        """
        Scan directory for video and subtitle files.

        Args:
            folder_path (str): Path to directory to scan
            skip_x_files (bool): Whether to skip files starting with 'x'

        Returns:
            tuple: (video_files, subtitle_files) lists
        """
        try:
            if not folder_path or not os.path.isdir(folder_path):
                print("Debug: Invalid folder path provided")
                return [], []

            # Clear file lists
            self.video_files = []
            self.subtitle_files = []
            self.matches = []

            # Video and subtitle extensions
            video_extensions = ['.mp4', '.mkv', '.avi', '.mov', '.wmv']
            subtitle_extensions = ['.srt', '.sub', '.idx', '.ass', '.ssa']

            # Scan files in directory
            files = os.listdir(folder_path)

            for file in files:
                file_path = os.path.join(folder_path, file)
                if os.path.isfile(file_path):
                    _, ext = os.path.splitext(file)
                    ext = ext.lower()

                    if ext in video_extensions:
                        self.video_files.append(file)
                    elif ext in subtitle_extensions:
                        self.subtitle_files.append(file)

            print(f"Debug: Found {len(self.video_files)} video files, {len(self.subtitle_files)} subtitle files")

            # Find matches
            self.find_matches(skip_x_files)

            return self.video_files, self.subtitle_files

        except Exception as e:
            print(f"Debug: Error scanning directory: {str(e)}")
            return [], []

    def find_matches(self, skip_x_files=False):
        """
        Find matches between video and subtitle files.

        Args:
            skip_x_files (bool): Whether to skip files starting with 'x'
        """
        try:
            # Clear matches
            self.matches = []

            # Track used subtitle files
            used_subtitles = set()

            # Filter out x-prefixed videos if option is active
            if skip_x_files:
                filtered_video_files = [v for v in self.video_files if not v.lower().startswith('x')]
            else:
                filtered_video_files = self.video_files

            # First find exact matches (file names same except extension)
            for video_file in filtered_video_files:
                video_name, _ = os.path.splitext(video_file)

                for subtitle_file in self.subtitle_files:
                    if subtitle_file in used_subtitles:
                        continue

                    subtitle_name, _ = os.path.splitext(subtitle_file)

                    # Exact match check
                    if video_name.lower() == subtitle_name.lower():
                        self.matches.append((video_file, subtitle_file))
                        used_subtitles.add(subtitle_file)
                        break

            # For videos without exact matches, calculate similarity scores
            unmatched_videos = [v for v in filtered_video_files if v not in [m[0] for m in self.matches]]

            # Store potential matches with scores
            potential_matches = []

            # Find potential subtitle matches for unmatched videos
            for video_file in unmatched_videos:
                video_name, _ = os.path.splitext(video_file)

                for subtitle_file in self.subtitle_files:
                    # Skip if subtitle already used
                    if subtitle_file in used_subtitles:
                        continue

                    subtitle_name, _ = os.path.splitext(subtitle_file)

                    # Calculate advanced similarity score
                    score = self.similarity_score(video_name, subtitle_name)

                    # Add as potential match if score above threshold
                    if score > 0.5:  # Threshold value
                        potential_matches.append((video_file, subtitle_file, score))

            # Sort potential matches by score (highest first)
            potential_matches.sort(key=lambda x: x[2], reverse=True)

            # Select best matches
            for video_file, subtitle_file, score in potential_matches:
                # Skip if video or subtitle already matched
                if (video_file in [m[0] for m in self.matches] or
                    subtitle_file in used_subtitles):
                    continue

                # Add match
                self.matches.append((video_file, subtitle_file))
                used_subtitles.add(subtitle_file)

            print(f"Debug: Found {len(self.matches)} matches out of {len(filtered_video_files)} videos")

        except Exception as e:
            print(f"Debug: Error finding matches: {str(e)}")

    def create_match(self, folder_path, video_file, subtitle_file):
        """
        Create or update a match between video and subtitle files.
        Adds '--' prefix to matched videos.

        Args:
            folder_path (str): Base folder path
            video_file (str): Video filename
            subtitle_file (str): Subtitle filename
        """
        try:
            # Add '--' prefix to video if not already present
            if not video_file.startswith('--'):
                old_path = os.path.join(folder_path, video_file)
                new_video_name = '--' + video_file
                new_path = os.path.join(folder_path, new_video_name)
                try:
                    os.rename(old_path, new_path)
                    video_file = new_video_name  # Use new name
                    # Update list
                    self.video_files = [new_video_name if v == video_file else v for v in self.video_files]
                    print(f"Debug: Added '--' prefix to {video_file}")
                except Exception as e:
                    print(f"Debug: Failed to rename file {video_file}: {str(e)}")
                    return

            # Copy all matches
            new_matches = []

            # Check existing matches for video and subtitle
            video_matched = False

            # Review all matches
            for v, s in self.matches:
                # If this is the video file, match with new subtitle
                if v == video_file:
                    new_matches.append((video_file, subtitle_file))
                    video_matched = True
                # If this is the subtitle file, skip (remove)
                elif s == subtitle_file:
                    continue
                # Keep other matches
                else:
                    new_matches.append((v, s))

            # If video was never matched, add new match
            if not video_matched:
                new_matches.append((video_file, subtitle_file))

            # Update matches list
            self.matches = new_matches

            print(f"Debug: Created match between '{video_file}' and '{subtitle_file}'")

        except Exception as e:
            print(f"Debug: Error creating match: {str(e)}")

    def remove_match(self, folder_path, video_file, subtitle_file):
        """
        Remove a match and remove '--' prefix from video if present.

        Args:
            folder_path (str): Base folder path
            video_file (str): Video filename
            subtitle_file (str): Subtitle filename
        """
        try:
            # Remove match if both video and subtitle exist
            if video_file and subtitle_file:
                for i, (v, s) in enumerate(self.matches):
                    if v == video_file and s == subtitle_file:
                        self.matches.pop(i)
                        # Remove '--' prefix from video if present
                        if video_file.startswith('--'):
                            old_path = os.path.join(folder_path, video_file)
                            new_name = video_file[2:]  # Remove '--'
                            new_path = os.path.join(folder_path, new_name)
                            try:
                                os.rename(old_path, new_path)
                                # Update list
                                self.video_files = [new_name if v == video_file else v for v in self.video_files]
                                print(f"Debug: Removed '--' prefix from {video_file}")
                            except Exception as e:
                                print(f"Debug: Failed to rename file {video_file}: {str(e)}")
                        return

        except Exception as e:
            print(f"Debug: Error removing match: {str(e)}")

    def rename_subtitles(self, folder_path):
        """
        Rename subtitle files to match their corresponding video files.

        Args:
            folder_path (str): Base folder path

        Returns:
            tuple: (renamed_count, errors) where errors is list of error messages
        """
        try:
            if not folder_path or not os.path.isdir(folder_path):
                return 0, ["Invalid folder path"]

            if not self.matches:
                return 0, ["No matches to rename"]

            renamed_count = 0
            errors = []

            for video_file, subtitle_file in self.matches:
                video_name, _ = os.path.splitext(video_file)
                _, subtitle_ext = os.path.splitext(subtitle_file)

                new_subtitle_name = video_name + subtitle_ext

                # Skip if new name is same as current
                if new_subtitle_name == subtitle_file:
                    continue

                try:
                    old_path = os.path.join(folder_path, subtitle_file)
                    new_path = os.path.join(folder_path, new_subtitle_name)

                    # Backup existing file if it exists
                    if os.path.exists(new_path):
                        backup_name = new_subtitle_name + ".bak"
                        backup_path = os.path.join(folder_path, backup_name)
                        os.rename(new_path, backup_path)

                    # Rename subtitle
                    os.rename(old_path, new_path)
                    renamed_count += 1
                    print(f"Debug: Renamed '{subtitle_file}' to '{new_subtitle_name}'")

                except Exception as e:
                    error_msg = f"{subtitle_file}: {str(e)}"
                    errors.append(error_msg)
                    print(f"Debug: Error renaming {error_msg}")

            return renamed_count, errors

        except Exception as e:
            error_msg = f"Unexpected error during rename: {str(e)}"
            print(f"Debug: {error_msg}")
            return 0, [error_msg]