import type { AnyModel, RenderProps } from '@anywidget/types';
import {
    css,
    html,
    LitElement,
    nothing,
    PropertyValues,
    TemplateResult,
} from 'lit';
import { property } from 'lit/decorators.js';
import { legacyStyles } from './ipywidgets_styles';
import { materialStyles } from './material_styles';
import { reverseMap } from './utils';

import './container';

export interface InspectorModel {
    hide_close_button: boolean;
    expand_points: boolean;
    expand_pixels: boolean;
    expand_objects: boolean;
    point_info: { [key: string]: any };
    pixel_info: { [key: string]: any };
    object_info: { [key: string]: any };
}

interface Node {
    label?: string;
    children?: Array<Node>;
    expanded?: boolean;
    topLevel?: boolean;
}

export class TreeNode extends LitElement {
    static get componentName() {
        return `tree-node`;
    }

    static styles = [
        legacyStyles,
        materialStyles,
        css`
            .node {
                align-items: center;
                cursor: pointer;
                display: flex;
            }

            .node-text {
                height: auto;
                line-height: 24px;
            }

            .node:hover {
                background-color: var(--jp-layout-color2);
                margin-left: -100%;
                padding-left: 100%;
            }

            .bullet {
                width: 24px;
            }

            .icon {
                width: 18px;
            }

            ul {
                list-style: none;
                padding-left: 24px;
                margin: 0;
            }
        `,
    ];

    @property() node: Node = {};
    @property({ reflect: true }) expanded: boolean = false;

    updated(changedProperties: Map<string, unknown>) {
        if (changedProperties.has('node') && this.node) {
            if ('expanded' in this.node) {
                this.expanded = this.node.expanded ?? false;
            }
        }
    }

    render() {
        return html`
            <div
                class="node ${this.expanded ? 'expanded' : ''}"
                @click="${this.toggleExpand}"
            >
                ${this.renderBullet()}
                ${this.renderIcon()}
                <span class="legacy-text node-text">${this.node.label}</span>
            </div>
            ${this.renderChildren()}
        `;
    }

    private toggleExpand() {
        this.expanded = !this.expanded;
    }

    private hasChildren(): boolean {
        return (this.node.children?.length ?? 0) > 0;
    }

    private renderChildren(): TemplateResult | typeof nothing {
        if (this.expanded && this.hasChildren()) {
            return html`<ul>${this.node.children?.map(this.renderChild)}</ul>`;
        }
        return nothing;
    }

    private renderChild(child: Node): TemplateResult {
        return html`<li><tree-node .node="${child}"></tree-node></li>`;
    }

    private renderBullet(): TemplateResult | typeof nothing {
        if (this.node.topLevel) {
            if (this.expanded) {
                return html`
                    <span class="bullet material-symbols-outlined">&#xe909;</span>
                `;
            }
            return html`<span class="bullet material-symbols-outlined">&#xe146;</span>`;
        } else if (this.hasChildren()) {
            if (this.expanded) {
                return html`
                    <span class="bullet material-symbols-outlined">&#xe15b;</span>
                `;
            }
            return html`<span class="bullet material-symbols-outlined">&#xe145;</span>`;
        }
        return html`<span class="bullet"></span>`;
    }

    private renderIcon(): TemplateResult | typeof nothing {
        if (this.node.topLevel) {
            return html`<span class="icon material-symbols-outlined">&#xe1a1;</span>`;
        } else if (this.hasChildren()) {
            if (this.expanded) {
                return html`
                    <span class="icon material-symbols-outlined">&#xe2c8;</span>
                `;
            }
            return html`<span class="icon material-symbols-outlined">&#xe2c7;</span>`;
        }
        return html`<span class="icon material-symbols-outlined">&#xe66d;</span>`;
    }
}

export class Inspector extends LitElement {
    static get componentName() {
        return `inspector-widget`;
    }

    static styles = [
        legacyStyles,
        css`
            .checkbox-container {
                align-items: center;
                display: flex;
                height: 32px;
            }

            .spacer {
                width: 8px;
            }

            .object-browser {
                max-height: 300px;
                overflow: scroll;
            }
        `,
    ];

    private _model: AnyModel<InspectorModel> | undefined = undefined;
    private static modelNameToViewName = new Map<
        keyof InspectorModel,
        keyof Inspector
    >([
        ['hide_close_button', 'hideCloseButton'],
        ['expand_points', 'expandPoints'],
        ['expand_pixels', 'expandPixels'],
        ['expand_objects', 'expandObjects'],
        ['point_info', 'pointInfo'],
        ['pixel_info', 'pixelInfo'],
        ['object_info', 'objectInfo'],
    ]);
    private static viewNameToModelName = reverseMap(this.modelNameToViewName);

    set model(model: AnyModel<InspectorModel>) {
        this._model = model;
        for (const [modelKey, widgetKey] of Inspector.modelNameToViewName) {
            if (widgetKey) {
                // Get initial values from the Python model.
                (this as any)[widgetKey] = model.get(modelKey);
                // Listen for updates to the model.
                model.on(`change:${modelKey}`, () => {
                    (this as any)[widgetKey] = model.get(modelKey);
                });
            }
        }
    }

    @property() hideCloseButton: boolean = false;
    @property() expandPoints: boolean = false;
    @property() expandPixels: boolean = true;
    @property() expandObjects: boolean = false;
    @property() pointInfo: Node = {};
    @property() pixelInfo: Node = {};
    @property() objectInfo: Node = {};

    render() {
        return html`
            <widget-container
                .hideCloseButton="${this.hideCloseButton}"
                @close-clicked="${this.onCloseButtonClicked}"
            >
                <div class="checkbox-container">
                    <span class="legacy-text">Expand</span>
                    <div class="spacer"></div>
                    <input
                        type="checkbox"
                        .checked="${this.expandPoints}"
                        @change="${this.onPointCheckboxEvent}"
                    />
                    <span class="legacy-text">Point</span>
                    <div class="spacer"></div>
                    <input
                        type="checkbox"
                        .checked="${this.expandPixels}"
                        @change="${this.onPixelCheckboxEvent}"
                    />
                    <span class="legacy-text">Pixels</span>
                    <div class="spacer"></div>
                    <input
                        type="checkbox"
                        .checked="${this.expandObjects}"
                        @change="${this.onFeatureCheckboxEvent}"
                    />
                    <span class="legacy-text">Objects</span>
                </div>
                <div class="object-browser">
                    ${this.renderNode(this.pointInfo)}
                    ${this.renderNode(this.pixelInfo)}
                    ${this.renderNode(this.objectInfo)}
                </div>
            </widget-container>
        `;
    }

    private renderNode(node: Node): TemplateResult | typeof nothing {
        if ((node.children?.length ?? 0) > 0) {
            return html`<tree-node .node="${node}"></tree-node> `;
        }
        return nothing;
    }

    private onPointCheckboxEvent(event: Event) {
        const target = event.target as HTMLInputElement;
        this.expandPoints = target.checked;
    }

    private onPixelCheckboxEvent(event: Event) {
        const target = event.target as HTMLInputElement;
        this.expandPixels = target.checked;
    }

    private onFeatureCheckboxEvent(event: Event) {
        const target = event.target as HTMLInputElement;
        this.expandObjects = target.checked;
    }

    private onCloseButtonClicked(_: Event) {
        this._model?.send({ "type": "click", "id": "close" });
    }

    updated(changedProperties: PropertyValues<Inspector>) {
        // Update the model properties so they're reflected in Python.
        for (const [viewProp, _] of changedProperties) {
            const castViewProp = viewProp as keyof Inspector;
            if (Inspector.viewNameToModelName.has(castViewProp)) {
                const modelProp = Inspector.viewNameToModelName.get(castViewProp);
                this._model?.set(modelProp as any, this[castViewProp] as any);
            }
        }
        this._model?.save_changes();
    }
}

// Without this check, there's a component registry issue when developing locally.
if (!customElements.get(TreeNode.componentName)) {
    customElements.define(TreeNode.componentName, TreeNode);
}
if (!customElements.get(Inspector.componentName)) {
    customElements.define(Inspector.componentName, Inspector);
}

async function render({ model, el }: RenderProps<InspectorModel>) {
    const inspector = document.createElement(
        Inspector.componentName,
    ) as Inspector;
    inspector.model = model;
    el.appendChild(inspector);
}

export default { render };
