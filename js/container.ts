import type { AnyModel, RenderProps } from '@anywidget/types';
import { css, html, LitElement, PropertyValues, TemplateResult } from 'lit';
import { property } from 'lit/decorators.js';
import { legacyStyles } from './ipywidgets_styles';
import { materialStyles } from './material_styles';
import { reverseMap } from './utils';

export interface ContainerModel {
    title: string;
    collapsed: boolean;
    hide_close_button: boolean;
}

export class Container extends LitElement {
    static get componentName() {
        return `widget-container`;
    }

    static styles = [
        legacyStyles,
        materialStyles,
        css`
            .header {
                display: flex;
                gap: 4px;
                margin: 4px;
            }

            .widget-container {
                margin: 4px;
            }

            .hidden {
                display: none;
            }

            .header-button {
                font-size: 16px;
                height: 28px;
                width: 28px;
            }

            .header-text {
                align-content: center;
                padding-left: 4px;
                padding-right: 4px;
            }
        `,
    ];

    private _model: AnyModel<ContainerModel> | undefined = undefined;
    private static modelNameToViewName = new Map<
        keyof ContainerModel,
        keyof Container
    >([
        ['collapsed', 'collapsed'],
        ['title', 'title'],
        ['hide_close_button', 'hideCloseButton'],
    ]);
    private static viewNameToModelName = reverseMap(
        Container.modelNameToViewName,
    );

    set model(model: AnyModel<ContainerModel>) {
        this._model = model;
        for (const [modelKey, widgetKey] of Container.modelNameToViewName) {
            // Get initial values from the Python model.
            (this as any)[widgetKey] = model.get(modelKey);
            // Listen for updates to the model.
            model.on(`change:${modelKey}`, () => {
                (this as any)[widgetKey] = model.get(modelKey);
            });
        }
    }

    @property() title: string = "";
    @property() collapsed: boolean = false;
    @property() hideCloseButton: boolean = false;

    render() {
        return html`
            <div class="header">
                <button
                    class="legacy-button primary header-button ${this.hideCloseButton ? 'hidden' : ''}"
                    @click="${this.onCloseButtonClicked}"
                >
                    <span class="material-symbols-outlined">&#xe5cd;</span>
                </button>
                <button
                    class="legacy-button header-button"
                    @click="${this.onCollapseToggled}"
                >
                    ${this.renderCollapseButtonIcon()}
                </button>
                <span
                    class="legacy-text header-text ${this.title ? '' : 'hidden'}"
                >
                    ${this.title}
                </span>
            </div>
            <div class="widget-container ${this.collapsed ? 'hidden' : ''}">
                <slot></slot>
            </div>
        `;
    }

    private onCloseButtonClicked(): void {
        this.dispatchEvent(new CustomEvent('close-clicked', {}));
    }

    private onCollapseToggled(): void {
        this.collapsed = !this.collapsed;
        this.dispatchEvent(new CustomEvent('collapse-clicked', {}));
    }

    private renderCollapseButtonIcon(): TemplateResult {
        if (this.collapsed) {
            return html`<span class="material-symbols-outlined">&#xf830;</span>`
        }
        return html`<span class="material-symbols-outlined">&#xf507;</span>`
    }

    updated(changedProperties: PropertyValues<Container>): void {
        // Update the model properties so they're reflected in Python.
        for (const [viewProp, _] of changedProperties) {
            const castViewProp = viewProp as keyof Container;
            if (Container.viewNameToModelName.has(castViewProp)) {
                const modelProp = Container.viewNameToModelName.get(castViewProp);
                this._model?.set(modelProp as any, this[castViewProp] as any);
            }
        }
        this._model?.save_changes();
    }
}

// Without this check, there's a component registry issue when developing locally.
if (!customElements.get(Container.componentName)) {
    customElements.define(Container.componentName, Container);
}

async function render({ model, el }: RenderProps<ContainerModel>) {
    const manager = document.createElement(Container.componentName) as Container;
    manager.model = model;
    el.appendChild(manager);
}

export default { render };
