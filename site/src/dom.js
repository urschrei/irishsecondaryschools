// Create an element. Attributes named "text" and "class" set the text
// content and class name. Children can be nodes, strings, or null.
export function h(tag, attributes = {}, children = []) {
  const node = document.createElement(tag);
  for (const [name, value] of Object.entries(attributes)) {
    if (value === null || value === undefined || value === false) continue;
    if (name === 'text') node.textContent = value;
    else if (name === 'class') node.className = value;
    else node.setAttribute(name, value === true ? '' : value);
  }
  node.append(...children.filter((child) => child !== null && child !== undefined));
  return node;
}

const SVG = 'http://www.w3.org/2000/svg';

export function svg(tag, attributes = {}, children = []) {
  const node = document.createElementNS(SVG, tag);
  for (const [name, value] of Object.entries(attributes)) {
    if (name === 'text') node.textContent = value;
    else node.setAttribute(name, value);
  }
  node.append(...children);
  return node;
}
