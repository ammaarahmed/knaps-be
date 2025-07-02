#!/usr/bin/env python3
"""
Demo script to show how to use the UUID-based CTC query utilities.
This script demonstrates the new normalized CTC structure with UUID support.
"""

import asyncio
import sys
import os

# Add the src directory to the path so we can import our modules
sys.path.append(os.path.join(os.path.dirname(__file__), 'src'))

from src.storage import CTCQueryHelper

async def demo_ctc_utilities():
    """Demonstrate the CTC query utilities."""
    helper = CTCQueryHelper()
    
    print("=== CTC Categories UUID Query Utilities Demo ===\n")
    
    # Get statistics
    print("1. Statistics:")
    stats = await helper.get_statistics()
    for key, value in stats.items():
        print(f"   {key}: {value}")
    
    print("\n2. Sample Hierarchy using UUIDs:")
    classes = await helper.get_all_classes()
    if classes:
        sample_class = classes[0]
        print(f"   Sample Class: {sample_class.name} (UUID: {sample_class.uuid})")
        
        # Get types using UUID
        types = await helper.get_types_by_class_uuid(sample_class.uuid)
        if types:
            sample_type = types[0]
            print(f"   Sample Type: {sample_type.name} (UUID: {sample_type.uuid})")
            
            # Get categories using UUID
            categories = await helper.get_categories_by_type_uuid(sample_type.uuid)
            if categories:
                sample_category = categories[0]
                print(f"   Sample Category: {sample_category.name} (UUID: {sample_category.uuid})")
                
                # Get category path using UUID
                path = await helper.get_category_path_by_uuid(sample_category.uuid)
                if path:
                    print("   Category Path:")
                    for i, cat in enumerate(path):
                        level_names = {1: "Class", 2: "Type", 3: "Category"}
                        level_name = level_names.get(cat.level, "Unknown")
                        print(f"     {i+1}. {level_name}: {cat.name} (UUID: {cat.uuid})")
    
    print("\n3. Search Example:")
    search_results = await helper.search_categories("BUP", level=1)
    if search_results:
        print(f"   Found {len(search_results)} categories matching 'BUP':")
        for result in search_results[:3]:  # Show first 3
            print(f"     - {result.name} (Level {result.level}, UUID: {result.uuid})")
    
    print("\n4. UUID-based Queries:")
    if classes:
        sample_class = classes[0]
        
        # Get children using UUID
        children = await helper.get_children_by_uuid(sample_class.uuid)
        print(f"   Children of {sample_class.name}: {len(children)} types")
        
        if children:
            sample_child = children[0]
            
            # Get parent using UUID
            parent = await helper.get_parent_by_uuid(sample_child.uuid)
            if parent:
                print(f"   Parent of {sample_child.name}: {parent.name}")
            
            # Get siblings using UUID
            siblings = await helper.get_siblings_by_uuid(sample_child.uuid)
            print(f"   Siblings of {sample_child.name}: {len(siblings)}")
    
    print("\n5. Full Hierarchy by UUID:")
    if classes:
        sample_class = classes[0]
        full_hierarchy = await helper.get_full_hierarchy_by_uuid(sample_class.uuid)
        if full_hierarchy:
            print(f"   Full hierarchy for {full_hierarchy.name}:")
            print_hierarchy(full_hierarchy)

def print_hierarchy(category, indent=0):
    """Print a category hierarchy in a tree-like format."""
    prefix = "  " * indent
    level_names = {1: "Class", 2: "Type", 3: "Category"}
    level_name = level_names.get(category.level, "Unknown")
    
    print(f"{prefix}{level_name}: {category.name} (UUID: {category.uuid})")
    
    if hasattr(category, 'children') and category.children:
        for child in category.children:
            print_hierarchy(child, indent + 1)

async def main():
    """Run the demo."""
    try:
        await demo_ctc_utilities()
        print("\nDemo completed successfully!")
    except Exception as e:
        print(f"Demo failed: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(main()) 