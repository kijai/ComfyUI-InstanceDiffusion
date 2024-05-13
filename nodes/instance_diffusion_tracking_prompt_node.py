from ..utils.prompt_utils import extract_prompts
from ..conditioning.instance_conditioning import InstanceConditioning


class InstanceDiffusionTrackingPromptNode:
    @classmethod
    def INPUT_TYPES(s):
        return {"required": {"positive": ("CONDITIONING", ),
                             "negative": ("CONDITIONING", ),
                             "clip": ("CLIP", ),
                             "tracking": ("TRACKING", ),
                             "positionnet": ("POSITIONNET", ),
                             "fusers": ("FUSERS", ),
                             "positive_text": ("STRING", {"multiline": True}),
                             "negative_text": ("STRING", {"multiline": True}),
                             },
                "optional": {
                                "masks": ("MASK",),
                            }
                }
    RETURN_TYPES = ("CONDITIONING", "CONDITIONING")
    RETURN_NAMES = ("positive", "negative")
    FUNCTION = "append"

    CATEGORY = "instance/conditioning"

    def _get_position_conds(self, clip, tracking, text, masks=None):
        # Get prompts and their class id and trakcer id
        prompt_pairs = extract_prompts(text)

        # Go through prompt pairs, encode prompts, and join with positions from tracking
        position_conds = []
        for tracker_id, class_id, prompt in prompt_pairs:
            _, cond_pooled = clip.encode_from_tokens(
                clip.tokenize(prompt), return_pooled=True)
            # A tracker_id of -1 means that it is prompting all instances of a single class
            tracker_ids = [tracker_id] if tracker_id != -1 else tracking[class_id]
    
            for t_id in tracker_ids:
                position_cond = {
                    'cond_pooled': cond_pooled,
                    'positions': tracking[class_id][t_id]
                }
                if masks is not None:
                    position_cond['instance_masks'] = masks

                position_conds.append(position_cond)

        return position_conds

    def _apply_position_conds(self, position_conds, conditioning, fusers, positionnet):
        # Add prompts+embeddings to the input conditionings
        cond_out = []
        for t in conditioning:
            n = [t[0], t[1].copy()]
            cond = n[1]
            prev = []
            has_instance = 'instance_diffusion' in cond
            instance_conditioning = cond['instance_diffusion'] if has_instance else InstanceConditioning(
                fusers, positionnet)
            cond['instance_diffusion'] = instance_conditioning
            instance_conditioning.add_conds(position_conds)

            cond['gligen'] = ('position', instance_conditioning, None)

            cond_out.append(n)

        return cond_out

    def append(self, positive, negative, clip, tracking, fusers, positionnet, positive_text, negative_text, fusers_batch_size=None, masks=None):

        positive_positions = self._get_position_conds(
            clip, tracking, positive_text, masks)
        positive = self._apply_position_conds(
            positive_positions, positive, fusers, positionnet)

        negative_positions = self._get_position_conds(
            clip, tracking, negative_text, masks)
        negative = self._apply_position_conds(
            negative_positions, negative, fusers, positionnet)

        return (positive, negative)
