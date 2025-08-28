"""
Internal linking module for KnowledgeHub.
Automatically creates links between related content.
"""
import os
import re
import sqlite3
from typing import List, Dict, Set, Tuple
from collections import Counter
import logging

class InternalLinker:
    """Manages automatic internal linking between content."""
    
    def __init__(self, db_manager):
        self.db_manager = db_manager
        self.link_pattern = r'\[\[([^\]]+)\]\]'  # [[Link Text]] format
        self.min_similarity_score = 0.3
    
    def find_related_content(self, content_id: int, max_links: int = 5) -> List[Dict]:
        """Find content related to the given content ID."""
        try:
            # Get the source content
            source_content = self.db_manager.get_content_metadata(content_id=content_id)
            if not source_content:
                return []
            
            source_tags = set(source_content.get('tags', []))
            source_title = source_content.get('title', '').lower()
            source_summary = source_content.get('summary', '').lower()
            
            # Get all other content
            all_content = self.db_manager.get_all_content()
            related_content = []
            
            for content in all_content:
                if content['id'] == content_id:
                    continue  # Skip self
                
                # Calculate similarity score
                score = self._calculate_similarity(
                    source_tags, 
                    source_title, 
                    source_summary,
                    content
                )
                
                if score >= self.min_similarity_score:
                    related_content.append({
                        'content': content,
                        'score': score,
                        'link_text': content['title'],
                        'file_path': content['file_path']
                    })
            
            # Sort by score and return top results
            related_content.sort(key=lambda x: x['score'], reverse=True)
            return related_content[:max_links]
            
        except Exception as e:
            logging.error(f"Error finding related content: {e}")
            return []
    
    def _calculate_similarity(self, source_tags: Set[str], source_title: str, 
                            source_summary: str, target_content: Dict) -> float:
        """Calculate similarity score between source and target content."""
        score = 0.0
        
        # Tag similarity (weighted heavily)
        target_tags = set(target_content.get('tags', []))
        if source_tags and target_tags:
            tag_overlap = len(source_tags.intersection(target_tags))
            tag_union = len(source_tags.union(target_tags))
            if tag_union > 0:
                score += (tag_overlap / tag_union) * 0.6
        
        # Title similarity
        target_title = target_content.get('title', '').lower()
        if source_title and target_title:
            title_words = set(source_title.split())
            target_words = set(target_title.split())
            if title_words and target_words:
                word_overlap = len(title_words.intersection(target_words))
                word_union = len(title_words.union(target_words))
                if word_union > 0:
                    score += (word_overlap / word_union) * 0.3
        
        # Summary/content similarity (basic keyword matching)
        target_summary = target_content.get('summary', '').lower()
        if source_summary and target_summary:
            source_keywords = self._extract_keywords(source_summary)
            target_keywords = self._extract_keywords(target_summary)
            if source_keywords and target_keywords:
                keyword_overlap = len(source_keywords.intersection(target_keywords))
                keyword_union = len(source_keywords.union(target_keywords))
                if keyword_union > 0:
                    score += (keyword_overlap / keyword_union) * 0.1
        
        return min(score, 1.0)  # Cap at 1.0
    
    def _extract_keywords(self, text: str, min_length: int = 4) -> Set[str]:
        """Extract keywords from text (simple implementation)."""
        # Remove common stop words and extract meaningful words
        stop_words = {
            'the', 'and', 'or', 'but', 'in', 'on', 'at', 'to', 'for', 'of', 'with',
            'by', 'from', 'up', 'about', 'into', 'through', 'during', 'before',
            'after', 'above', 'below', 'between', 'among', 'within', 'without',
            'this', 'that', 'these', 'those', 'is', 'are', 'was', 'were', 'be',
            'been', 'being', 'have', 'has', 'had', 'do', 'does', 'did', 'will',
            'would', 'could', 'should', 'may', 'might', 'must', 'can', 'shall'
        }
        
        words = re.findall(r'\b[a-z]+\b', text.lower())
        keywords = {
            word for word in words 
            if len(word) >= min_length and word not in stop_words
        }
        
        return keywords
    
    def add_internal_links(self, file_path: str) -> bool:
        """Add internal links to a markdown file."""
        try:
            # Get content metadata
            content_metadata = self.db_manager.get_content_metadata(file_path=file_path)
            if not content_metadata:
                logging.warning(f"No metadata found for {file_path}")
                return False
            
            # Find related content
            related_content = self.find_related_content(content_metadata['id'])
            if not related_content:
                return False
            
            # Read the current file
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
            
            # Check if links already exist
            existing_links = re.findall(self.link_pattern, content)
            existing_titles = {link.lower() for link in existing_links}
            
            # Add internal links section
            links_to_add = []
            for item in related_content:
                title = item['content']['title']
                if title.lower() not in existing_titles:
                    relative_path = os.path.relpath(item['file_path'], os.path.dirname(file_path))
                    links_to_add.append(f"- [[{title}]]({relative_path})")
            
            if links_to_add:
                # Add links section at the end
                links_section = f"\n\n---\n\n## 🔗 Related Content\n\n" + "\n".join(links_to_add)
                
                # Check if related content section already exists
                if "## 🔗 Related Content" not in content:
                    content += links_section
                    
                    # Write back to file
                    with open(file_path, 'w', encoding='utf-8') as f:
                        f.write(content)
                    
                    logging.info(f"Added {len(links_to_add)} internal links to {file_path}")
                    return True
            
            return False
            
        except Exception as e:
            logging.error(f"Error adding internal links to {file_path}: {e}")
            return False
    
    def update_all_internal_links(self) -> Dict[str, int]:
        """Update internal links for all content in the knowledge vault."""
        results = {"updated": 0, "skipped": 0, "errors": 0}
        
        try:
            all_content = self.db_manager.get_all_content()
            
            for content in all_content:
                try:
                    if os.path.exists(content['file_path']):
                        if self.add_internal_links(content['file_path']):
                            results["updated"] += 1
                        else:
                            results["skipped"] += 1
                    else:
                        results["errors"] += 1
                        logging.warning(f"File not found: {content['file_path']}")
                        
                except Exception as e:
                    results["errors"] += 1
                    logging.error(f"Error processing {content['file_path']}: {e}")
            
            return results
            
        except Exception as e:
            logging.error(f"Error updating internal links: {e}")
            return results
    
    def find_broken_links(self) -> List[Dict]:
        """Find broken internal links in the knowledge vault."""
        broken_links = []
        
        try:
            all_content = self.db_manager.get_all_content()
            
            for content in all_content:
                if not os.path.exists(content['file_path']):
                    continue
                
                try:
                    with open(content['file_path'], 'r', encoding='utf-8') as f:
                        file_content = f.read()
                    
                    # Find all internal links
                    links = re.findall(self.link_pattern, file_content)
                    
                    for link in links:
                        # Check if linked content exists
                        linked_content = self.db_manager.search_content(link, search_type='title')
                        if not linked_content:
                            broken_links.append({
                                'source_file': content['file_path'],
                                'source_title': content['title'],
                                'broken_link': link
                            })
                
                except Exception as e:
                    logging.error(f"Error checking links in {content['file_path']}: {e}")
            
            return broken_links
            
        except Exception as e:
            logging.error(f"Error finding broken links: {e}")
            return []
    
    def suggest_new_links(self, content_id: int) -> List[Dict]:
        """Suggest new internal links based on content analysis."""
        try:
            content = self.db_manager.get_content_metadata(content_id=content_id)
            if not content:
                return []
            
            # Read file content
            if not os.path.exists(content['file_path']):
                return []
            
            with open(content['file_path'], 'r', encoding='utf-8') as f:
                file_content = f.read()
            
            # Extract key terms from content
            key_terms = self._extract_key_terms(file_content)
            
            # Find content that mentions these terms
            suggestions = []
            all_content = self.db_manager.get_all_content()
            
            for other_content in all_content:
                if other_content['id'] == content_id:
                    continue
                
                # Check if other content contains these terms
                other_title = other_content.get('title', '').lower()
                other_summary = other_content.get('summary', '').lower()
                
                for term in key_terms:
                    if (term in other_title or term in other_summary) and \
                       other_content['title'] not in [s['title'] for s in suggestions]:
                        suggestions.append({
                            'title': other_content['title'],
                            'file_path': other_content['file_path'],
                            'matching_term': term,
                            'reason': f"Contains term: '{term}'"
                        })
            
            return suggestions[:10]  # Return top 10 suggestions
            
        except Exception as e:
            logging.error(f"Error suggesting new links: {e}")
            return []
    
    def _extract_key_terms(self, content: str) -> List[str]:
        """Extract key terms from content for link suggestions."""
        # Simple extraction of capitalized terms and important phrases
        terms = []
        
        # Find capitalized words (potential topics)
        capitalized = re.findall(r'\b[A-Z][a-z]+(?:\s+[A-Z][a-z]+)*\b', content)
        terms.extend([term.lower() for term in capitalized if len(term) > 3])
        
        # Find quoted terms
        quoted = re.findall(r'"([^"]+)"', content)
        terms.extend([term.lower() for term in quoted if len(term) > 3])
        
        # Remove duplicates and return most common
        term_counts = Counter(terms)
        return [term for term, count in term_counts.most_common(20)]