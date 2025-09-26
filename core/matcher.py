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

    def scan_folder(self, folder_path, skip_x=False, algorithm_name=None):
        """
        Scan a folder for video and subtitle files and find matches.

        Args:
            folder_path (str): Path to the folder to scan
            skip_x (bool): Whether to skip files starting with 'x'
            algorithm_name (str): Name of the algorithm to use for matching
        """
        try:
            import os
            import glob

            # Clear previous results
            self.video_files = []
            self.subtitle_files = []
            self.matches = []

            # Video file extensions
            video_extensions = ['.mp4', '.mkv', '.avi', '.mov', '.wmv', '.flv', '.webm']
            # Subtitle file extensions
            subtitle_extensions = ['.srt', '.sub', '.ass', '.ssa', '.vtt']

            # Find all files
            all_files = []
            for root, dirs, files in os.walk(folder_path):
                for file in files:
                    full_path = os.path.join(root, file)
                    rel_path = os.path.relpath(full_path, folder_path)

                    # Skip files starting with x if requested
                    if skip_x and file.startswith('x'):
                        continue

                    all_files.append(rel_path)

            # Separate video and subtitle files
            for file in all_files:
                file_lower = file.lower()
                if any(file_lower.endswith(ext) for ext in video_extensions):
                    self.video_files.append(file)
                elif any(file_lower.endswith(ext) for ext in subtitle_extensions):
                    self.subtitle_files.append(file)

            # Find matches using the default algorithm
            self.find_matches(algorithm_name)

            print(f"Debug: Found {len(self.video_files)} videos, {len(self.subtitle_files)} subtitles, {len(self.matches)} matches")

        except Exception as e:
            print(f"Debug: Error scanning folder: {str(e)}")

    def find_matches(self, algorithm_name=None):
        """
        Find matches between video and subtitle files using the specified algorithm.

        Args:
            algorithm_name (str): Name of the algorithm to use. If None, uses default.
        """
        try:
            # Get the algorithm to use
            algorithms = self.get_all_algorithms()
            if algorithm_name and algorithm_name in algorithms:
                algorithm_func = algorithms[algorithm_name]
                algorithm_display_name = algorithm_name
            else:
                # Default to Algorithm 1 (Year + Word)
                algorithm_func = self.algorithm_1_year_word_matching
                algorithm_display_name = "Algorithm 1 (Year + Word)"

            matches = self.find_matches_with_algorithm(algorithm_func, threshold=0.5)

            # Convert to the expected format (video_file, subtitle_file)
            self.matches = [(video, sub) for video, sub, score in matches]

            print(f"Debug: Found {len(self.matches)} matches using {algorithm_display_name}")

        except Exception as e:
            print(f"Debug: Error finding matches: {str(e)}")

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

            # Extract and compare year information (critical for movie matching)
            year_pattern = r'\b(19|20)\d{2}\b'
            str1_years = re.findall(year_pattern, str1)
            str2_years = re.findall(year_pattern, str2)

            # If both have years and they don't match, significantly reduce score
            if str1_years and str2_years:
                if not set(str1_years).intersection(set(str2_years)):
                    print(f"Debug: Different years detected - {str1_years} vs {str2_years}, reducing score")
                    return 0.1  # Very low score for different years

            # Extract source information (BluRay, HDTV, WEB-DL, etc.)
            source_patterns = [
                r'\bblu-?ray\b', r'\bhdtv\b', r'\bweb-?dl\b', r'\bwebrip\b',
                r'\bdvdrip\b', r'\bbrrip\b', r'\bhdrip\b', r'\brtc\b'
            ]

            str1_sources = []
            str2_sources = []

            for pattern in source_patterns:
                if re.search(pattern, str1):
                    str1_sources.extend(re.findall(pattern, str1))
                if re.search(pattern, str2):
                    str2_sources.extend(re.findall(pattern, str2))

            # If both have different sources, reduce score
            if str1_sources and str2_sources:
                if not set(str1_sources).intersection(set(str2_sources)):
                    print(f"Debug: Different sources detected - {str1_sources} vs {str2_sources}, reducing score")
                    return 0.2  # Low score for different sources

            # Remove release group tags (everything after last dash if it looks like a group)
            # But be more conservative - only remove known release group patterns
            str1_clean = str1
            str2_clean = str2

            # Remove common release group patterns at the end (more specific)
            release_patterns = [
                r'-[A-Z]{2,}[0-9]*$',  # Groups like -AOC, -SMURF, -YTS
                r'-[A-Z0-9]{4,}$',     # Longer alphanumeric groups
            ]

            for pattern in release_patterns:
                str1_clean = re.sub(pattern, '', str1_clean)
                str2_clean = re.sub(pattern, '', str2_clean)

            # Remove common technical terms that shouldn't affect matching
            technical_terms = [
                r'\b720p\b', r'\b1080p\b', r'\b2160p\b', r'\b4k\b',
                r'\bx264\b', r'\bx265\b', r'\bh264\b', r'\bh265\b',
                r'\baac\b', r'\bac3\b', r'\bdts\b', r'\bflac\b',
                r'\bddp5\.1\b', r'\batmos\b', r'\bsdr\b', r'\bhdr10\b',
                r'\b10bit\b', r'\bsilence\b'
            ]

            for term in technical_terms:
                str1_clean = re.sub(term, '', str1_clean, flags=re.IGNORECASE)
                str2_clean = re.sub(term, '', str2_clean, flags=re.IGNORECASE)

            # Clean up extra spaces and normalize
            str1_clean = ' '.join(str1_clean.split())
            str2_clean = ' '.join(str2_clean.split())

            print(f"Debug: Cleaned names - '{str1_clean}' vs '{str2_clean}'")

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
                str1_match = re.search(pattern, str1_clean)
                if str1_match:
                    if len(str1_match.groups()) == 2:
                        str1_season = int(str1_match.group(1))
                        str1_episode = int(str1_match.group(2))
                    else:
                        str1_episode = int(str1_match.group(1))
                    break

            for pattern in season_ep_patterns:
                str2_match = re.search(pattern, str2_clean)
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

            # Use cleaned strings for further comparison
            str1 = str1_clean
            str2 = str2_clean

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

            # Word-based similarity using cleaned strings
            words1 = set(re.findall(r'\w+', str1))
            words2 = set(re.findall(r'\w+', str2))

            # Remove very short words (likely noise)
            words1 = {w for w in words1 if len(w) > 2}
            words2 = {w for w in words2 if len(w) > 2}

            if words1 and words2:
                # Common word ratio
                common_words = words1.intersection(words2)
                word_similarity = len(common_words) / max(len(words1), len(words2))

                # Require minimum number of common words for movies (not episodes)
                min_common_words = 2 if not (str1_season or str1_episode) else 1
                if len(common_words) < min_common_words:
                    print(f"Debug: Insufficient common words ({len(common_words)}), reducing score")
                    return 0.1

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

    def similarity_score_algorithm1(self, str1, str2):
        """
        Algorithm 1: Year-based + Word matching algorithm.
        - Treats 4-digit numbers as years (except 1080, 2160)
        - Checks word overlap for movie titles
        - Requires 90% title similarity

        Args:
            str1 (str): First string
            str2 (str): Second string

        Returns:
            float: Similarity score between 0.0 and 1.0
        """
        try:
            str1 = str1.lower()
            str2 = str2.lower()

            # Exact match
            if str1 == str2:
                return 1.0

            # Extract years (4-digit numbers except 1080, 2160)
            year_pattern = r'\b(19|20)\d{2}\b'
            str1_years = set(re.findall(year_pattern, str1))
            str2_years = set(re.findall(year_pattern, str2))

            # If both have years and they don't match, very low score
            if str1_years and str2_years and not str1_years.intersection(str2_years):
                return 0.1

            # Extract words (excluding years and technical terms)
            words1 = set(re.findall(r'\b\w+\b', str1))
            words2 = set(re.findall(r'\b\w+\b', str2))

            # Remove years and technical terms
            exclude_terms = {'1080', '2160', '720', '480', 'x264', 'x265', 'h264', 'h265',
                           'aac', 'ac3', 'dts', 'flac', 'bluray', 'webdl', 'hdtv', 'dvdrip'}
            words1 = words1 - str1_years - exclude_terms
            words2 = words2 - str2_years - exclude_terms

            # Remove short words
            words1 = {w for w in words1 if len(w) > 2}
            words2 = {w for w in words2 if len(w) > 2}

            if not words1 or not words2:
                return 0.0

            # Calculate word overlap
            common_words = words1.intersection(words2)
            total_unique = words1.union(words2)

            if not total_unique:
                return 0.0

            word_overlap_ratio = len(common_words) / len(total_unique)

            # Require minimum overlap for movies
            if word_overlap_ratio < 0.5:
                return 0.1

            # High overlap = high score
            if word_overlap_ratio > 0.8:
                return 0.9

            return word_overlap_ratio * 0.8 + 0.1

        except Exception as e:
            print(f"Debug: Error in Algorithm 1: {str(e)}")
            return 0.0

    def similarity_score_algorithm2(self, str1, str2):
        """
        Algorithm 2: Sequence similarity weighted algorithm.
        - Heavily weights difflib sequence matcher
        - Good for similar strings with small differences

        Args:
            str1 (str): First string
            str2 (str): Second string

        Returns:
            float: Similarity score between 0.0 and 1.0
        """
        try:
            str1 = str1.lower()
            str2 = str2.lower()

            # Exact match
            if str1 == str2:
                return 1.0

            # Clean strings (remove technical terms)
            technical_terms = [
                r'\b720p\b', r'\b1080p\b', r'\b2160p\b', r'\b4k\b',
                r'\bx264\b', r'\bx265\b', r'\bh264\b', r'\bh265\b',
                r'\baac\b', r'\bac3\b', r'\bdts\b', r'\bflac\b'
            ]

            for term in technical_terms:
                str1 = re.sub(term, '', str1)
                str2 = re.sub(term, '', str2)

            str1 = ' '.join(str1.split())
            str2 = ' '.join(str2.split())

            # Sequence similarity (high weight)
            sequence_similarity = difflib.SequenceMatcher(None, str1, str2).ratio()

            # Word overlap (low weight)
            words1 = set(re.findall(r'\b\w+\b', str1))
            words2 = set(re.findall(r'\b\w+\b', str2))
            words1 = {w for w in words1 if len(w) > 2}
            words2 = {w for w in words2 if len(w) > 2}

            if words1 and words2:
                common_words = words1.intersection(words2)
                word_similarity = len(common_words) / max(len(words1), len(words2))
            else:
                word_similarity = 0

            # Weighted combination
            final_score = sequence_similarity * 0.8 + word_similarity * 0.2

            return final_score

        except Exception as e:
            print(f"Debug: Error in Algorithm 2: {str(e)}")
            return 0.0

    def similarity_score_algorithm3(self, str1, str2):
        """
        Algorithm 3: Levenshtein distance weighted algorithm.
        - Heavily weights edit distance similarity
        - Good for strings with character-level differences

        Args:
            str1 (str): First string
            str2 (str): Second string

        Returns:
            float: Similarity score between 0.0 and 1.0
        """
        try:
            str1 = str1.lower()
            str2 = str2.lower()

            # Exact match
            if str1 == str2:
                return 1.0

            # Clean strings
            technical_terms = [
                r'\b720p\b', r'\b1080p\b', r'\b2160p\b', r'\b4k\b',
                r'\bx264\b', r'\bx265\b', r'\bh264\b', r'\bh265\b',
                r'\baac\b', r'\bac3\b', r'\bdts\b', r'\bflac\b'
            ]

            for term in technical_terms:
                str1 = re.sub(term, '', str1)
                str2 = re.sub(term, '', str2)

            str1 = ' '.join(str1.split())
            str2 = ' '.join(str2.split())

            # Levenshtein similarity (high weight)
            max_len = max(len(str1), len(str2))
            if max_len > 0:
                levenshtein_similarity = 1 - (self.levenshtein_distance(str1, str2) / max_len)
            else:
                levenshtein_similarity = 0

            # Character overlap (low weight)
            common_chars = sum(1 for c in str1 if c in str2)
            char_similarity = common_chars / max(len(str1), len(str2)) if max(len(str1), len(str2)) > 0 else 0

            # Weighted combination
            final_score = levenshtein_similarity * 0.7 + char_similarity * 0.3

            return final_score

        except Exception as e:
            print(f"Debug: Error in Algorithm 3: {str(e)}")
            return 0.0

    def similarity_score_algorithm4(self, str1, str2):
        """
        Algorithm 4: Word overlap weighted algorithm.
        - Heavily weights word-based similarity
        - Good for titles with different technical details

        Args:
            str1 (str): First string
            str2 (str): Second string

        Returns:
            float: Similarity score between 0.0 and 1.0
        """
        try:
            str1 = str1.lower()
            str2 = str2.lower()

            # Exact match
            if str1 == str2:
                return 1.0

            # Extract and compare year information
            year_pattern = r'\b(19|20)\d{2}\b'
            str1_years = set(re.findall(year_pattern, str1))
            str2_years = set(re.findall(year_pattern, str2))

            # Different years = low score
            if str1_years and str2_years and not str1_years.intersection(str2_years):
                return 0.1

            # Extract words
            words1 = set(re.findall(r'\b\w+\b', str1))
            words2 = set(re.findall(r'\b\w+\b', str2))

            # Remove technical terms and years
            exclude_terms = {'1080', '2160', '720', '480', 'x264', 'x265', 'h264', 'h265',
                           'aac', 'ac3', 'dts', 'flac', 'bluray', 'webdl', 'hdtv', 'dvdrip',
                           'brrip', 'hdrip', 'rtc', 'p', 'web', 'dl'}
            words1 = words1 - str1_years - exclude_terms
            words2 = words2 - str2_years - exclude_terms

            # Remove short words
            words1 = {w for w in words1 if len(w) > 2}
            words2 = {w for w in words2 if len(w) > 2}

            if not words1 or not words2:
                return 0.0

            # Word overlap metrics
            common_words = words1.intersection(words2)
            union_words = words1.union(words2)

            # Jaccard similarity (intersection over union)
            jaccard_similarity = len(common_words) / len(union_words) if union_words else 0

            # Common word ratio
            common_ratio = len(common_words) / max(len(words1), len(words2))

            # Require minimum common words
            if len(common_words) < 2:
                return 0.1

            # Weighted combination
            final_score = jaccard_similarity * 0.6 + common_ratio * 0.4

            return final_score

        except Exception as e:
            print(f"Debug: Error in Algorithm 4: {str(e)}")
            return 0.0

    def test_algorithms(self, video_files, subtitle_files, threshold=0.5):
        """
        Test all 4 algorithms and show success rates.

        Args:
            video_files (list): List of video filenames
            subtitle_files (list): List of subtitle filenames
            threshold (float): Similarity threshold for matching

        Returns:
            dict: Results for each algorithm
        """
        try:
            results = {
                'algorithm1': {'matches': 0, 'total_possible': 0, 'success_rate': 0.0},
                'algorithm2': {'matches': 0, 'total_possible': 0, 'success_rate': 0.0},
                'algorithm3': {'matches': 0, 'total_possible': 0, 'success_rate': 0.0},
                'algorithm4': {'matches': 0, 'total_possible': 0, 'success_rate': 0.0},
                'current': {'matches': 0, 'total_possible': 0, 'success_rate': 0.0}
            }

            # Test each video against each subtitle
            for video in video_files:
                video_name = os.path.splitext(video)[0]

                for subtitle in subtitle_files:
                    subtitle_name = os.path.splitext(subtitle)[0]

                    # Skip if names are identical (perfect match)
                    if video_name.lower() == subtitle_name.lower():
                        continue

                    results['current']['total_possible'] += 1
                    results['algorithm1']['total_possible'] += 1
                    results['algorithm2']['total_possible'] += 1
                    results['algorithm3']['total_possible'] += 1
                    results['algorithm4']['total_possible'] += 1

                    # Test current algorithm
                    current_score = self.similarity_score(video_name, subtitle_name)
                    if current_score >= threshold:
                        results['current']['matches'] += 1

                    # Test Algorithm 1
                    score1 = self.similarity_score_algorithm1(video_name, subtitle_name)
                    if score1 >= threshold:
                        results['algorithm1']['matches'] += 1

                    # Test Algorithm 2
                    score2 = self.similarity_score_algorithm2(video_name, subtitle_name)
                    if score2 >= threshold:
                        results['algorithm2']['matches'] += 1

                    # Test Algorithm 3
                    score3 = self.similarity_score_algorithm3(video_name, subtitle_name)
                    if score3 >= threshold:
                        results['algorithm3']['matches'] += 1

                    # Test Algorithm 4
                    score4 = self.similarity_score_algorithm4(video_name, subtitle_name)
                    if score4 >= threshold:
                        results['algorithm4']['matches'] += 1

            # Calculate success rates
            for algo in results:
                if results[algo]['total_possible'] > 0:
                    results[algo]['success_rate'] = (results[algo]['matches'] / results[algo]['total_possible']) * 100

            return results

        except Exception as e:
            print(f"Debug: Error testing algorithms: {str(e)}")
            return {}

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

    def algorithm_1_year_word_matching(self, str1, str2):
        """
        Algorithm 1: Year + Word matching
        - Extract 4-digit numbers (excluding 1080, 2160 as resolutions)
        - Treat them as years and require year match
        - Match common words between filenames
        - Simple and effective for movie matching

        Args:
            str1 (str): First filename
            str2 (str): Second filename

        Returns:
            float: Similarity score 0.0-1.0
        """
        try:
            str1 = str1.lower()
            str2 = str2.lower()

            # Extract 4-digit numbers, exclude known resolutions
            year_pattern = r'\b(19|20)\d{2}\b'
            str1_years = set(re.findall(year_pattern, str1))
            str2_years = set(re.findall(year_pattern, str2))

            # Remove resolution numbers from year candidates
            resolutions = {'1080', '2160'}
            str1_years = str1_years - resolutions
            str2_years = str2_years - resolutions

            # If both have years and no common years, very low score
            if str1_years and str2_years and not str1_years.intersection(str2_years):
                return 0.1

            # Extract words (split by common separators)
            words1 = set(re.findall(r'\b\w+\b', str1))
            words2 = set(re.findall(r'\b\w+\b', str2))

            # Remove common technical words that shouldn't affect matching
            technical_words = {
                'bluray', 'blu', 'ray', 'hdtv', 'web', 'dl', 'webrip', 'dvdrip',
                'brrip', 'hdrip', 'rtc', 'x264', 'x265', 'h264', 'h265', 'aac',
                'ac3', 'dts', 'flac', 'ddp5', '1', 'atmos', 'sdr', 'hdr10',
                '10bit', 'silence', '720p', '1080p', '2160p', '4k', 'mp4',
                'mkv', 'avi', 'srt', 'sub', 'subs', 'subtitle', 'video'
            }

            words1 = words1 - technical_words
            words2 = words2 - technical_words

            # Calculate word overlap
            if not words1 or not words2:
                return 0.0

            common_words = words1.intersection(words2)
            total_unique_words = words1.union(words2)

            if not total_unique_words:
                return 0.0

            word_similarity = len(common_words) / len(total_unique_words)

            # Boost score if years match
            if str1_years.intersection(str2_years):
                word_similarity = min(1.0, word_similarity + 0.3)

            return word_similarity

        except Exception as e:
            print(f"Debug: Error in algorithm_1: {str(e)}")
            return 0.0

    def algorithm_2_sequence_matching(self, str1, str2):
        """
        Algorithm 2: Sequence matching using difflib
        - Uses Python's difflib for sequence similarity
        - Good for detecting typos and small variations
        - Considers the order of characters

        Args:
            str1 (str): First filename
            str2 (str): Second filename

        Returns:
            float: Similarity score 0.0-1.0
        """
        try:
            # Clean strings - remove extensions and common separators
            str1_clean = re.sub(r'\.(mp4|mkv|avi|srt|sub)$', '', str1.lower())
            str2_clean = re.sub(r'\.(mp4|mkv|avi|srt|sub)$', '', str2.lower())

            # Remove technical terms
            technical_terms = [
                r'\b720p\b', r'\b1080p\b', r'\b2160p\b', r'\b4k\b',
                r'\bx264\b', r'\bx265\b', r'\bh264\b', r'\bh265\b',
                r'\baac\b', r'\bac3\b', r'\bdts\b', r'\bflac\b',
                r'\bbluray\b', r'\bhdtv\b', r'\bweb-?dl\b'
            ]

            for term in technical_terms:
                str1_clean = re.sub(term, '', str1_clean, flags=re.IGNORECASE)
                str2_clean = re.sub(term, '', str2_clean, flags=re.IGNORECASE)

            # Clean up spaces
            str1_clean = ' '.join(str1_clean.split())
            str2_clean = ' '.join(str2_clean.split())

            # Use difflib sequence matcher
            matcher = difflib.SequenceMatcher(None, str1_clean, str2_clean)
            similarity = matcher.ratio()

            # Boost if they share common substrings
            if str1_clean in str2_clean or str2_clean in str1_clean:
                similarity = min(1.0, similarity + 0.2)

            return similarity

        except Exception as e:
            print(f"Debug: Error in algorithm_2: {str(e)}")
            return 0.0

    def algorithm_3_levenshtein_based(self, str1, str2):
        """
        Algorithm 3: Levenshtein distance based
        - Uses edit distance for similarity calculation
        - Good for detecting character-level differences
        - Normalized by string length

        Args:
            str1 (str): First filename
            str2 (str): Second filename

        Returns:
            float: Similarity score 0.0-1.0
        """
        try:
            # Clean strings similar to algorithm 2
            str1_clean = re.sub(r'\.(mp4|mkv|avi|srt|sub)$', '', str1.lower())
            str2_clean = re.sub(r'\.(mp4|mkv|avi|srt|sub)$', '', str2.lower())

            technical_terms = [
                r'\b720p\b', r'\b1080p\b', r'\b2160p\b', r'\b4k\b',
                r'\bx264\b', r'\bx265\b', r'\bh264\b', r'\bh265\b',
                r'\baac\b', r'\bac3\b', r'\bdts\b', r'\bflac\b',
                r'\bbluray\b', r'\bhdtv\b', r'\bweb-?dl\b'
            ]

            for term in technical_terms:
                str1_clean = re.sub(term, '', str1_clean, flags=re.IGNORECASE)
                str2_clean = re.sub(term, '', str2_clean, flags=re.IGNORECASE)

            str1_clean = ' '.join(str1_clean.split())
            str2_clean = ' '.join(str2_clean.split())

            # Calculate Levenshtein distance
            distance = self.levenshtein_distance(str1_clean, str2_clean)
            max_len = max(len(str1_clean), len(str2_clean))

            if max_len == 0:
                return 1.0 if str1_clean == str2_clean else 0.0

            # Normalize similarity (1 - normalized_distance)
            similarity = 1 - (distance / max_len)

            # Ensure non-negative
            similarity = max(0.0, similarity)

            return similarity

        except Exception as e:
            print(f"Debug: Error in algorithm_3: {str(e)}")
            return 0.0

    def algorithm_4_hybrid_approach(self, str1, str2):
        """
        Algorithm 4: Hybrid approach
        - Combines multiple similarity metrics
        - Uses weighted combination of different approaches
        - Most sophisticated algorithm

        Args:
            str1 (str): First filename
            str2 (str): Second filename

        Returns:
            float: Similarity score 0.0-1.0
        """
        try:
            # Get scores from other algorithms
            score1 = self.algorithm_1_year_word_matching(str1, str2)
            score2 = self.algorithm_2_sequence_matching(str1, str2)
            score3 = self.algorithm_3_levenshtein_based(str1, str2)

            # Weighted combination
            # Year+word matching gets highest weight, others complementary
            weights = [0.5, 0.3, 0.2]
            hybrid_score = (score1 * weights[0] + score2 * weights[1] + score3 * weights[2])

            # Extract year information for bonus
            year_pattern = r'\b(19|20)\d{2}\b'
            str1_years = set(re.findall(year_pattern, str1.lower()))
            str2_years = set(re.findall(year_pattern, str2.lower()))

            resolutions = {'1080', '2160'}
            str1_years = str1_years - resolutions
            str2_years = str2_years - resolutions

            # Year match bonus
            if str1_years.intersection(str2_years):
                hybrid_score = min(1.0, hybrid_score + 0.2)
            elif str1_years and str2_years:  # Both have years but different
                hybrid_score = max(0.0, hybrid_score - 0.3)

            # Ensure bounds
            hybrid_score = max(0.0, min(1.0, hybrid_score))

            return hybrid_score

        except Exception as e:
            print(f"Debug: Error in algorithm_4: {str(e)}")
            return 0.0

    def get_all_algorithms(self):
        """
        Get all available matching algorithms.

        Returns:
            dict: Dictionary of algorithm names to functions
        """
        return {
            "Algorithm 1 (Year + Word)": self.algorithm_1_year_word_matching,
            "Algorithm 2 (Sequence)": self.algorithm_2_sequence_matching,
            "Algorithm 3 (Levenshtein)": self.algorithm_3_levenshtein_based,
            "Algorithm 4 (Hybrid)": self.algorithm_4_hybrid_approach
        }

    def find_matches_with_algorithm(self, algorithm_func, threshold=0.5):
        """
        Find matches using a specific algorithm.

        Args:
            algorithm_func: Algorithm function to use
            threshold (float): Minimum similarity score for match

        Returns:
            list: List of (video_file, subtitle_file, score) tuples
        """
        matches = []

        for video_file in self.video_files:
            best_match = None
            best_score = 0.0

            for subtitle_file in self.subtitle_files:
                score = algorithm_func(video_file, subtitle_file)
                if score > best_score and score >= threshold:
                    best_score = score
                    best_match = subtitle_file

            if best_match:
                matches.append((video_file, best_match, best_score))

        return matches