from flask import Blueprint, request, jsonify
from llm_models.bloom import bloom_llm

llm_blueprint = Blueprint('llm', __name__)

tokenizer, model = bloom_llm()

@llm_blueprint.route("/invoke", methods=["POST"])
def invoke():
    data = request.json
    prompt = data.get("prompt", "")
    inputs = tokenizer(prompt, return_tensors="pt")
    outputs = model.generate(inputs.input_ids, max_length=512, temperature=0.7)
    response = tokenizer.decode(outputs[0], skip_special_tokens=True)
    return jsonify({"response": response})

@llm_blueprint.route("/test", methods=["GET"])
def test_func():
    return jsonify({"response": "This is a test"})