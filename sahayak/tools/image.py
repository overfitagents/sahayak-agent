import base64
import glob
import os
from typing import Dict, Optional

import google.genai.types as types
from google.adk.tools.tool_context import ToolContext
from google import genai
from google.genai.types import GenerateContentConfig, Modality
from io import BytesIO
import asyncio

import concurrent.futures

async def create_slide_images(
    tool_context: Optional[ToolContext] = None,
) -> Dict[str, any]:
    """
    Create images for each slide using Gemini's image generation API and update slide contents.
    Returns:
        Dict[str, any]: Dictionary containing status, message and slide contents
    """
    print("Starting create_slide_images function")
    try:
        slide_contents = tool_context.state.get("slide_contents", {})
        if not slide_contents:
            print("No slide contents found in tool context state")
            return {
                "status": "error",
                "message": "No slide contents found in tool context state"
            }

        slides = slide_contents.get("slides", [])
        if not slides:
            print("No slides found in slide contents")
            return {"status": "error", "message": "No slides found in slide contents"}

        print(f"Processing {len(slides)} slides")
        client = genai.Client()
        generation_config = GenerateContentConfig(
            response_modalities=[Modality.TEXT, Modality.IMAGE]
        )

        async def process_slide(index: int, slide: dict):
            try:
                print(f"Generating image for slide {index}: {slide.get('content', '')[:50]}...")

                response = client.models.generate_content(
                    model="gemini-2.0-flash-preview-image-generation",
                    contents=slide.get("image_description", ""),
                    config=generation_config,
                )

                for part in response.candidates[0].content.parts:
                    if part.inline_data:
                        image_bytes = part.inline_data.data

                        root_image_dir = "generated_images"
                        if not os.path.exists(root_image_dir):
                            os.makedirs(root_image_dir)

                        filename = f"slide_image_{index}.png"
                        filepath = os.path.join(root_image_dir, filename)
                        print(f"Saving image as {filepath}")

                        with open(filepath, "wb") as f:
                            f.write(image_bytes)

                        image_artifact = types.Part.from_bytes(
                            data=image_bytes, mime_type="image/png"
                        )

                        artifact_version = await tool_context.save_artifact(
                            filename=filename,
                            artifact=image_artifact
                        )

                        slide["image_filename"] = filename
                        slide["image_version"] = artifact_version

                return slide
            except Exception as e:
                print(f"Error processing slide {index}: {str(e)}")
                return slide

        # Process slides in parallel
        tasks = [process_slide(index, slide) for index, slide in enumerate(slides, 1)]
        updated_slides = await asyncio.gather(*tasks)

        print("Updating slide contents")
        slide_contents["slides"] = updated_slides
        tool_context.state["slide_contents"] = slide_contents

        print("Successfully completed image generation", slide_contents)
        return {
            "status": "success",
            "message": "Images generated and slides updated",
            "slide_contents": slide_contents
        }

    except Exception as e:
        print(f"Fatal error in create_slide_images: {str(e)}")
        return {"status": "error", "message": f"Error creating images: {str(e)}"}


def create_slide_images_test(
) -> Dict[str, any]:
    """
    Create images for each slide using Gemini's image generation API and update slide contents.
    Returns:
        Dict[str, any]: Dictionary containing status, message and slide contents
    """
    print("Starting create_slide_images function")
    try:
        slide_contents = {"slides": [
            {
              "heading": "Introduction to Science and the Power of Observation",
              "points": [
                "Chapter 1: The Wonderful World of Science",
                "Grade 6 Science"
              ],
              "image_description": "A vibrant, eye-catching image representing curiosity and discovery. Perhaps a magnifying glass over a globe, or a student with a thought bubble filled with scientific symbols, against a backdrop of a classroom at St. Xavier's High School in Solapur."
            },
            {
              "heading": "What is Science? More Than Just Facts!",
              "points": [
                "Science is a dynamic process for understanding our world, not just a collection of facts.",
                "It involves actively 'thinking' about phenomena, 'observing' details, and 'doing' experiments or investigations.",
                "Science is present all around us, from how our mobile phones work to the growth of plants in Solapur's climate."
              ],
              "image_description": "A collage or infographic showing different aspects of science: a brain representing thinking, an eye representing observation, hands doing an experiment, and everyday objects like a plant, a lightbulb, and a bicycle wheel, symbolizing science in daily life."
            },
            {
              "heading": "The Power of Observation",
              "points": [
                "Keen observation is the fundamental skill that allows us to notice details and identify patterns in the world.",
                "It helps us discover new things and gather information, which is crucial for scientific inquiry.",
                "Just like during our 'Curiosity Walk' in the St. Xavier's High School garden, careful observation opens up questions about 'why' or 'how' things work."
              ],
              "image_description": "A high-quality real-world photo of a student from St. Xavier's High School, Solapur, intently observing a plant, an insect, or a natural phenomenon with a magnifying glass in a garden or schoolyard setting."
            },
            {
              "heading": "Curiosity: The Starting Point of Discovery",
              "points": [
                "Curiosity is the driving force behind all scientific discovery, sparking the desire to know more.",
                "Asking 'why' and 'how' questions is absolutely fundamental to starting any scientific investigation.",
                "From a pen not writing to a wilting plant, curiosity helps us approach everyday problems with a scientific mindset, like the one we used to brainstorm solutions today."
              ],
              "image_description": "A conceptual image showing a question mark transforming into a lightbulb or a magnifying glass, symbolizing curiosity leading to ideas and discovery. It should convey a sense of wonder and inquiry."
            },
            {
              "heading": "Your Scientific Journey Begins!",
              "points": [
                "Science is an exhilarating adventure of continuous observation, thoughtful questioning, and active exploration.",
                "Every observation you make and every 'why' or 'how' you ask contributes to your scientific understanding.",
                "Keep fostering your natural curiosity – it's your most powerful tool in the wonderful world of science!"
              ],
              "image_description": "An inspiring image of a diverse group of young students, perhaps from different backgrounds, looking excitedly at something, possibly a diagram or a simple experiment, with a sense of wonder and teamwork. The background could subtly suggest a school environment like St. Xavier's."
            }
          ]
        }

        if not slide_contents:
            print("No slide contents found in tool context state")
            return {
                "status": "error",
                "message": "No slide contents found in tool context state",
            }

        slides = slide_contents.get("slides", [])
        if not slides:
            print("No slides found in slide contents")
            return {"status": "error", "message": "No slides found in slide contents"}

        print(f"Processing {len(slides)} slides")
        # Initialize the client
        client = genai.Client()
        # model = client.get_model("gemini-2.0-flash-preview-image-generation")
        generation_config = GenerateContentConfig(
            response_modalities=[Modality.TEXT, Modality.IMAGE]
        )

        def generate_image_for_slide(slide):
            try:
                print(f"Generating image for slide: {slide.get('content', '')[:50]}...")
                contents = [
                    {"role": "user", "parts": [{"text": slide.get("content", "")}]}
                ]

                # response = model.generate_content(
                #     contents=contents, generation_config=generation_config
                # )

                response = client.models.generate_content(
                    model="gemini-2.0-flash-preview-image-generation",
                    contents=slide.get("image_description", ""),
                    config=generation_config,
                )
                print(response)

                for part in response.candidates[0].content.parts:
                    if part.inline_data:
                        image_data = BytesIO(part.inline_data.data)
                        image_bytes = image_data.getvalue()

                        # Save the image to a file
                        print("Saving image to file")
                        if not os.path.exists("slide_images"):
                            os.makedirs("slide_images")
                        os.chdir("slide_images")
                        # Generate a unique filename
                        # to avoid overwriting existing images
                        # This is a simple way to generate unique filenames 
                        # based on the number of existing images
                        if not glob.glob("slide_image_*.png"):
                            filename = "slide_image_1.png"
                        else:
                            # Generate a new filename based on existing files
                            existing_files = glob.glob("slide_image_*.png")
                            if existing_files:
                                last_file = max(existing_files, key=os.path.getctime)
                                last_index = int(last_file.split("_")[-1].split(".")[0])
                                filename = f"slide_image_{last_index + 1}.png"
                            else:
                                filename = "slide_image_1.png"

                        print(f"Saving image as {filename}")
                        with open(filename, "wb") as img_file:
                            img_file.write(image_bytes)

                        filename = (
                            f"slide_image_{len(glob.glob('slide_image_*.png')) + 1}.png"
                        )
                        print(f"Saving image as {filename}")
                        image_artifact = types.Part(
                            inline_data=types.Blob(
                                data=image_bytes, mime_type="image/png"
                            )
                        )

                        # artifact_version = tool_context.save_artifact(
                        #     filename=filename, artifact=image_artifact
                        # )

                        slide["image_filename"] = filename
                        # slide["image_version"] = artifact_version
                        return slide

                return slide
            except Exception as e:
                print(f"Error processing slide: {str(e)}")
                return slide

        print("Starting parallel processing of slides")
        with concurrent.futures.ThreadPoolExecutor() as executor:
            updated_slides = list(executor.map(generate_image_for_slide, slides))

        print("Updating slide contents")
        slide_contents["slides"] = updated_slides
        # tool_context.state["slide_contents"] = slide_contents

        print("Successfully completed image generation", slide_contents)
        return {
            "status": "success",
            "message": "Images generated and slides updated",
            "slide_contents": slide_contents,
        }

    except Exception as e:
        print(f"Fatal error in create_slide_images: {str(e)}")
        return {"status": "error", "message": f"Error creating images: {str(e)}"}
