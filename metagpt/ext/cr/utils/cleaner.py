"""Cleaner."""

from unidiff import Hunk, PatchedFile, PatchSet

from metagpt.logs import logger


def rm_patch_useless_part(patch: PatchSet, used_suffix: list[str] = ["java", "py"]) -> PatchSet:
    new_patch = PatchSet("")
    useless_files = []
    for pfile in patch:
        suffix = str(pfile.target_file).split(".")[-1]
        if suffix not in used_suffix or pfile.is_removed_file:
            useless_files.append(pfile.path)
            continue
        new_patch.append(pfile)
    logger.info(f"total file num: {len(patch)}, used file num: {len(new_patch)}, useless_files: {useless_files}")
    return new_patch


def add_line_num_on_patch(patch: PatchSet, start_line_num: int = 1) -> PatchSet:
    new_patch = PatchSet("")
    lineno = start_line_num
    for pfile in patch:
        new_pfile = PatchedFile(
            source=pfile.source_file,
            target=pfile.target_file,
            source_timestamp=pfile.source_timestamp,
            target_timestamp=pfile.target_timestamp,
        )
        for hunk in pfile:
            arr = [str(line) for line in hunk]
            new_hunk = Hunk(
                src_start=hunk.source_start,
                src_len=hunk.source_length,
                tgt_start=hunk.target_start,
                tgt_len=hunk.target_length,
                section_header=hunk.section_header,
            )

            for line in arr:
                # if len(line) > 0 and line[0] in ["+", "-"]:
                #     line = f"{lineno} {line}"
                #     lineno += 1
                line = f"{lineno} {line}"
                lineno += 1
                new_hunk.append(line)
            new_pfile.append(new_hunk)
        new_patch.append(new_pfile)
    return new_patch


def get_code_block_from_patch(patch: PatchSet, code_start_line: str, code_end_line: str) -> str:
    line_arr = str(patch).split("\n")
    code_arr = []
    add_line_tag = False
    for line in line_arr:
        if line.startswith(f"{code_start_line} "):
            add_line_tag = True

        if add_line_tag:
            new_line = " ".join(line.split(" ")[1:])  # rm line-no tag
            code_arr.append(new_line)

        if line.startswith(f"{code_end_line} "):
            add_line_tag = False

    return "\n".join(code_arr)
