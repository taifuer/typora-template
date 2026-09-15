-- Center standalone, uncaptioned images in DOCX exports, including native AST input.
-- Captioned figures already use the reference document's figure styles.
if FORMAT ~= 'docx' then
  return {}
end

local function center_blocks(blocks)
  for index, block in ipairs(blocks) do
    if block.t == 'Para' and #block.content == 1 then
      local picture = block.content[1]
      if picture.t == 'Link' and #picture.content == 1 then
        picture = picture.content[1]
      end
      if picture.t == 'Image' and not picture.title:match('^fig:') then
        blocks[index] = pandoc.Div({block}, pandoc.Attr('', {}, {['custom-style'] = 'Figure'}))
      end
    elseif block.t == 'BlockQuote' or (block.t == 'Div' and not block.attributes['custom-style']) then
      block.content = center_blocks(block.content)
      blocks[index] = block
    elseif block.t == 'BulletList' or block.t == 'OrderedList' then
      for item_index, item in ipairs(block.content) do
        block.content[item_index] = center_blocks(item)
      end
      blocks[index] = block
    end
    -- Leave explicit styles, table cells, and Pandoc 3 Figure blocks intact.
  end
  return blocks
end

return {{
  Pandoc = function(document)
    document.blocks = center_blocks(document.blocks)
    return document
  end,
}}
