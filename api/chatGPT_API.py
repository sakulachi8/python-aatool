import os
import openai
openai.organization = ""
openai.api_key = ""

def chatGPT(text):
    completion = openai.ChatCompletion.create(
                    model="gpt-3.5-turbo-16k",
                    messages=[
                        {"role": "system", "content": "You are a helpful assistant for a wealth manager"},
                        {"role": "user", "content": text}
                    ],
                     temperature=1,
                    max_tokens=256,
                    top_p=1,
                    frequency_penalty=0,
                    presence_penalty=0
                    )
    return print(completion['choices'][0]['message']['content'])

chatGPT("My client has a large portfolio of commercial and residential realestate. Our view is that the property market may suffer a decline and suggest that the client moves to cash and certain other assets, such as long term government bonds and large caps like AAPL and Microsoft. Provide me a high level summarry of this that can be used at the start of a report.")

''' EXAMPLE OUTPUT:

Executive Summary:

In light of potential market disruptions in the real estate industry, we recommend a strategic shift towards more stable assets. Our analysis suggests that moving away from commercial and residential real estate holdings and allocating to cash, long-term government bonds, and blue-chip stocks such as Apple (AAPL) and Microsoft (MSFT) could help mitigate the potential downside risks associated with a property market decline.

Background:

Client X currently holds a significant portfolio of commercial and residential real estate assets. However, our team has identified concerning indicators that suggest the property market may face a decline, potentially resulting in financial loss for our client. To protect and preserve the client's wealth, we have analyzed alternative investment opportunities that offer stability and potential growth.

Investment Strategy:

Our proposed strategy involves rebalancing the client's portfolio by reducing exposure to the real estate sector and redistributing funds into less volatile and potentially more profitable options. This includes considering cash as a safe harbor, long-term government bonds as fixed-income instruments, and blue-chip stocks such as Apple and Microsoft as stable equity investments.

Benefits:

1. Cash: Holding a position in cash provides immediate liquidity, allowing for quick deployment of capital in promising opportunities that may arise during or after a market decline.

2. Long-Term Government Bonds'''