"""
Chart Generator Service
Menggenerate chart Superset menggunakan AI model berdasarkan user prompt dan dataset.

Usage:
    from app.services.chart_generator import ChartGenerator
    
    generator = ChartGenerator()
    result = await generator.generate_chart(
        user_prompt="Buat pie chart untuk data status", 
        dataset_selected=dataset_data
    )
"""

from .chart_generator import ChartGenerator, ChartGeneratorError
from .instruction_builder import InstructionBuilder
from .constants import CHART_TYPES, CHART_CONFIGS

__all__ = [
    'ChartGenerator', 
    'ChartGeneratorError',
    'InstructionBuilder',
    'CHART_TYPES', 
    'CHART_CONFIGS'
]