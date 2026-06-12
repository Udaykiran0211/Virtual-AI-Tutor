from utils.llm_api import extract_json
import json

def test_extract():
    # Test case 1: Markdown background with object
    text1 = "Here is the result: ```json\n{\"key\": \"value\"}\n``` hope that helps."
    res1 = extract_json(text1)
    print(f"Test 1: {res1}")
    assert json.loads(res1) == {"key": "value"}

    # Test case 2: Markdown background with array (Crucial fix)
    text2 = "Check this out: ```json\n[{\"q\": 1}, {\"q\": 2}]\n```"
    res2 = extract_json(text2)
    print(f"Test 2: {res2}")
    assert json.loads(res2) == [{"q": 1}, {"q": 2}]

    # Test case 3: Raw object
    text3 = "   {\"a\": 1}   "
    res3 = extract_json(text3)
    print(f"Test 3: {res3}")
    assert json.loads(res3) == {"a": 1}

    # Test case 4: Raw array
    text4 = "[1, 2, 3]"
    res4 = extract_json(text4)
    print(f"Test 4: {res4}")
    assert json.loads(res4) == [1, 2, 3]

    print("All extraction tests passed!")

if __name__ == "__main__":
    test_extract()
