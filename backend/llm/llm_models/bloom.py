from transformers import AutoTokenizer, AutoModelForCausalLM

def bloom_llm():
    model_name = "bigscience/bloom-560m"
    tokenizer = AutoTokenizer.from_pretrained(model_name)
    model = AutoModelForCausalLM.from_pretrained(model_name)

    return tokenizer, model