# Public export method

The public corpus was created from the accepted local evidence by explicit
allowlisting. Raw provider result wrappers were never copied. The projector
retained experiment coordinates, responses (including exact answer/segment text
and annotations/links), model identity, relevant numeric usage, and safe attempt
status. It omitted stdout/stderr wrappers, session/request identifiers,
timestamps, local paths, transcripts, launch logs, credentials, and board or
agent-runtime state.

`artifacts/projection-manifest.json` records both each private raw byte hash and
the corresponding public projection hash. `raw_allowed_content_sha256` and
`projection_allowed_content_sha256` are computed over cell ID, status, and
response; their equality is the content-preservation check. The public files have
different bytes by design and are not represented as raw archives.

Several narrative or judgment artifacts were also projected to remove local
paths and orchestration identifiers while preserving findings. Their original
and public hashes are listed below. V1 `aggregate.json` required no change.

| Artifact | Original SHA-256 | Public SHA-256 | Projection |
| --- | --- | --- | --- |
| `artifacts/v2/aggregate.json` | `65e7e7950913d5bf0b1da466cd1edc96de0c89ac5cacaf1f3cc943c54052e126` | `f6a7c7df7ffe00610d98f55231e725ffa8c158c456c31cc9cd1553e78e838be0` | Local review path replaced; review hash points to the sanitized public judgment file |
| `artifacts/v2/independent-link-review.json` | `3ed569d02f17a79647fe59ca799d5ba4ba9f3cd56ed7d91f5daef6c9286a2674` | `8fde9aa93aee6a3723b04a80d9cbd82a5d44ff5399e5f7474e105700c06f699f` | Board task ID removed; all 27 judgments retained |
| `docs/v1-report.md` | `4ca088f14c0529d2c1e0cfcb37d647883be90ce5feda1dda91edbd999188eb66` | `21ff35e6c9b7b447be2824e44b287bafd676c6b0d7f503a74e444a1acd72f8d7` | Local artifact/log paths and orchestration note removed; full historical object and unmerged status clarified |
| `docs/v2-report.md` | `a5abef160df00b049adadc25e2dacb471aeb6170f6fe8c89bc1ca2a4baa15394` | `688fc5b56a5663632ad394abb2caa74b3de78144e96a10bebf68830fe1f9392c` | Local artifact/archive paths and orchestration note removed |
| `docs/reviews/v1-final-review.md` | `21c6c368455f2cdc22ed923b0242fa06369fcf9522ae7b1abd21226d3214dc49` | `3dc43178875649a5bee6edcbd01ade9d2913ae304a72458427786f559da0d912` | Board ID and private path labels removed |
| `docs/reviews/v2-final-review.md` | `5e3909477cc7e35283da0b668b6b682375ba4fb62d1f60f8c9ca5ff65037d7c4` | `3360e5fce16da09e6a22253a7e53ae54c01fe0ef5d87e61a6168e874ce571209` | Board ID and private path labels removed |
| `docs/reviews/v2-rereview.md` | `95b7a366389be73c41920c32908ddf5ee329954fe3135a28690196df956f6ceb` | `0469e8e000452b151b4d6ad074b3137862a539b7360b22aa250ddecc06da93ed` | Board ID and private path labels removed |

The release gate checks the actual candidate file list. Its negative control
plants a forbidden local path into a candidate copy and requires rejection; the
projection test separately plants a provider-wrapper field and requires the
allowlist validator to reject it.

Credential checks are deliberately bounded: known credential filename classes
and representative high-confidence key/private-key formats are refused, while
an explicit placeholder example and a harmless `task-output-source` near-match
are admitted. This is a publication backstop, not universal secret detection.

The frozen accepted v1/v2 source maps retain the abbreviated historical object
name recorded during the study. The authoritative full object name and its
status as an unmerged research candidate are documented in
`THIRD_PARTY_NOTICES.md`; this provenance clarification does not rewrite the
accepted maps or fixtures.
