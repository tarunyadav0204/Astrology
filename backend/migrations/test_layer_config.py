import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(__file__)))

from chat.PromptConfig.layer_config_service import LayerConfigService

def test_layer_configuration():
    """Test layer configuration retrieval"""
    
    service = LayerConfigService()
    
    categories = ['career', 'health', 'marriage', 'wealth', 'progeny', 'education', 'timing', 'general']
    
    print("=" * 80)
    print("LAYER CONFIGURATION TEST")
    print("=" * 80)
    
    for category in categories:
        print(f"\n{'='*80}")
        print(f"CATEGORY: {category.upper()}")
        print(f"{'='*80}")
        
        config = service.get_category_configuration(category)
        
        print(f"\n📊 Required Layers ({len(config['required_layers'])}):")
        for layer in config['required_layers']:
            print(f"   ✓ {layer['layer_name']} ({layer['layer_key']})")
        
        print(f"\n📋 Required Fields ({len(config['required_fields'])}):")
        for field in config['required_fields']:
            size_kb = field['estimated_size_bytes'] / 1024
            print(f"   • {field['field_key']}: {size_kb:.1f} KB [{field['layer_key']}]")
        
        print(f"\n📈 Required Divisional Charts ({len(config['required_divisional_charts'])}):")
        for chart in config['required_divisional_charts']:
            print(f"   • {chart['chart_name']} ({chart['chart_key']})")
        
        print(f"\n🚀 Transit Configuration:")
        print(f"   • Max Activations: {config['transit_limits']['max_transit_activations']}")
        print(f"   • Include Macro Transits: {'Yes' if config['transit_limits']['include_macro_transits'] else 'No'}")
        print(f"   • Include Navatara Warnings: {'Yes' if config['transit_limits']['include_navatara_warnings'] else 'No'}")
        
        # Calculate estimated size
        size_info = service.get_estimated_context_size(category)
        print(f"\n💾 Estimated Context Size:")
        print(f"   • Fields: {size_info['field_size_bytes'] / 1024:.1f} KB")
        print(f"   • Charts: {size_info['chart_size_bytes'] / 1024:.1f} KB")
        print(f"   • Transits: {size_info['transit_size_bytes'] / 1024:.1f} KB")
        print(f"   • TOTAL: {size_info['total_size_kb']} KB")
        print(f"   • Reduction: {size_info['reduction_percent']}% (vs 251 KB baseline)")
    
    print(f"\n{'='*80}")
    print("SUMMARY")
    print(f"{'='*80}")
    
    for category in categories:
        size_info = service.get_estimated_context_size(category)
        print(f"{category.ljust(12)}: {str(size_info['total_size_kb']).rjust(6)} KB  ({size_info['reduction_percent']}% reduction)")

if __name__ == "__main__":
    test_layer_configuration()
