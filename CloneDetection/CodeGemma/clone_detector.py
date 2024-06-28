# clone_detector.py
from transformers import AutoTokenizer, AutoModelForCausalLM
import torch

class CloneDetector:
    def __init__(self, model_id, device, dtype=torch.bfloat16):
        self.device = device
        self.dtype = dtype
        self.tokenizer = AutoTokenizer.from_pretrained(model_id)
        self.model = AutoModelForCausalLM.from_pretrained(
            model_id,
            torch_dtype=self.dtype,
        ).to(self.device)

    def get_response(self, code1, code2):
        chat = [
            { "role": "user", "content": f"""Judge the following two codes whether is a clone pair. \
            There are two types of simple clone: one is the exact same code snippet, and the other is the replacement of class names, parameter names, and variable names, but the order of replacement remains unchanged. \
                Structural clone means that after the input data enters the model, the data flow, i.e., the shape transformation process, is similar.\
                    Answer only as YES/NO.
            ###Code1
            {code1}
            ###Code2
            {code2} """},
        ]

        prompt = self.tokenizer.apply_chat_template(chat, tokenize=False, add_generation_prompt=True)
        inputs = self.tokenizer.encode(prompt, add_special_tokens=False, return_tensors="pt").to(self.device)
        outputs = self.model.generate(input_ids=inputs, max_new_tokens=4, do_sample=False)
        prompt_len = inputs.shape[-1]
        response = self.tokenizer.decode(outputs[0][prompt_len:], skip_special_tokens=True)

        return response

        # return response
