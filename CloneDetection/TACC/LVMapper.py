# import mmh3

# def get_murmurhash(lines):
#     combined_lines = '\n'.join(lines)
#     return mmh3.hash128(combined_lines)

def get_filter_similarity(hash1, hash2):
    common_hashes = set(hash1) & set(hash2)
    S = len(common_hashes)
    max_len = max(len(hash1), len(hash2))
    similarity = S / max_len
    return similarity

def locate_clones(inverted_index, hash_dict):
    threshold_high=0.7
    threshold_low=0
    clone_pairs = []
    second_level_candidates = []
    compared_pairs = set()
    Sim_list = []
    for func_id, hash_values in hash_dict.items():
        seen_hashes = set()
        for hash_value in hash_values:
            if hash_value in inverted_index and hash_value not in seen_hashes:
                for candidate_func_id in inverted_index[hash_value]:
                    if func_id == candidate_func_id or (func_id, candidate_func_id) in compared_pairs or (candidate_func_id, func_id) in compared_pairs:
                        continue
                    candidate_hash_values = hash_dict[candidate_func_id]
                    similarity = get_filter_similarity(hash_values, candidate_hash_values)
                    print(similarity)
                    if similarity >= threshold_high:
                        # print(f"First level clone pair: {func_id} and {candidate_func_id}  Similarity {similarity}")
                        clone_pairs.append((func_id, candidate_func_id))
                        Sim_list.append(similarity)
                    elif threshold_low < similarity <= threshold_high:
                        second_level_candidates.append((func_id, candidate_func_id))
                    compared_pairs.add((func_id, candidate_func_id))
                seen_hashes.add(hash_value)

    return clone_pairs, Sim_list, second_level_candidates



