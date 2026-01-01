"""sd.cpp-webui - LoRA selector UI component"""

import os
import gradio as gr
from modules.shared_instance import config
from modules.loader import get_models


def create_lora_selector_ui():
    """Create LoRA selector UI with insert functionality"""
    
    lora_dir = config.get('lora_dir')
    
    def get_lora_list():
        """Get list of LoRA files without extensions"""
        loras = get_models(lora_dir)
        return [os.path.splitext(lora)[0] for lora in loras]
    
    def insert_lora(current_prompt, lora_name, strength):
        """Insert LoRA tag into prompt"""
        if not lora_name:
            return current_prompt
        
        lora_tag = f"<lora:{lora_name}:{strength}>"
        
        if current_prompt:
            return f"{current_prompt} {lora_tag}"
        return lora_tag
    
    def refresh_loras():
        """Refresh LoRA list"""
        return gr.update(choices=get_lora_list())
    
    with gr.Accordion(label="LoRA Selector", open=False):
        with gr.Row():
            lora_dropdown = gr.Dropdown(
                label="Select LoRA",
                choices=get_lora_list(),
                interactive=True,
                allow_custom_value=False
            )
            lora_strength = gr.Slider(
                label="Strength",
                minimum=0.0,
                maximum=2.0,
                value=0.8,
                step=0.05
            )
        with gr.Row():
            insert_btn = gr.Button(value="Insert to Prompt", size="sm")
            refresh_btn = gr.Button(value="🔄", size="sm")
    
    return {
        'lora_dropdown': lora_dropdown,
        'lora_strength': lora_strength,
        'insert_btn': insert_btn,
        'refresh_btn': refresh_btn,
        'insert_lora_fn': insert_lora,
        'refresh_loras_fn': refresh_loras
    }
