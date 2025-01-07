import type { RenderProps } from "@anywidget/types";
import { css, html, HTMLTemplateResult, nothing, TemplateResult } from "lit";
import { property } from "lit/decorators.js";

import { legacyStyles } from "./ipywidgets_styles";
import { LitWidget } from "./lit_widget";
import { materialStyles } from "./styles";
import { classMap } from "lit/directives/class-map.js";

export interface ContainerModel {
    icon: string;
    title: string;
    collapsed: boolean;
    hide_close_button: boolean;
}

export class Container extends LitWidget<ContainerModel, Container> {
    static get componentName(): string {
        return `widget-container`;
    }

    static styles = [
        legacyStyles,
        materialStyles,
        css`
            div {
                background-color: var(--colab-primary-surface-color, --jp-layout-color1, white);
            }

            .header {
                display: flex;
                gap: 4px;
                padding: 4px;
            }

            .icon {
                align-items: center;
                display: flex;
                font-size: 20px;
                height: 28px;
                justify-content: center;
            }

            .widget-container {
                padding: 4px;
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
                flex-grow: 1;
                padding: 0 6px 0 12px;
            }
        `,
    ];

    @property({ type: String }) icon: string = "";
    @property({ type: String }) title: string = "";
    @property({ type: Boolean }) collapsed: boolean = false;
    @property({ type: Boolean }) hideCloseButton: boolean = false;
    @property({ type: Boolean }) compactMode: boolean = false;

    modelNameToViewName(): Map<keyof ContainerModel, keyof Container | null> {
        return new Map([
            ["icon", "icon"],
            ["collapsed", "collapsed"],
            ["title", "title"],
            ["hide_close_button", "hideCloseButton"],
        ]);
    }

    render() {
        return html`
            ${this.compactMode ? this.renderCompactHeader() : html`
                <div class="header">
                    ${this.renderIcon()}
                    ${this.title ? this.renderTitle() : nothing}
                    ${this.renderCollapseButton()}
                    ${this.renderCloseButton()}
                </div>
            `}
            <div class="widget-container ${this.collapsed ? "hidden" : ""}">
                <slot></slot>
            </div>
        `;
    }

    private renderCompactHeader(): TemplateResult {
        return html`<div class="header">
            ${this.renderCollapseButton()}
            ${(this.title && !this.collapsed) ? this.renderTitle() : nothing}
            ${this.renderCloseButton()}
        </div>`;
    }

    private renderCloseButton(): HTMLTemplateResult | typeof nothing {
        if (this.hideCloseButton) {
            return nothing;
        }
        return html`
            <button
                class="legacy-button primary header-button"
                @click="${this.onCloseButtonClicked}"
            >
                <span class="material-symbols-outlined">&#xe5cd;</span>
            </button>
        `;
    }

    private renderTitle(): HTMLTemplateResult {
        return html`<span class="legacy-text header-text">${this.title}</span>`;
    }

    private onCloseButtonClicked(): void {
        this.dispatchEvent(new CustomEvent("close-clicked", {}));
    }

    private onCollapseToggled(): void {
        this.collapsed = !this.collapsed;
        this.dispatchEvent(new CustomEvent("collapse-clicked", {}));
    }

    private renderIcon(): TemplateResult {
        return html`<span class="icon material-symbols-outlined">
                        ${this.icon}
                    </span>`
    }

    private renderCollapseButton(): TemplateResult {
        let icon: TemplateResult;
        if (this.compactMode) {
            icon = this.renderIcon();
        } else if (this.collapsed) {
            icon = html`<span class="material-symbols-outlined"
                >&#xf830;</span
            >`;
        } else {
            icon = html`<span class="material-symbols-outlined">&#xf507;</span>`;
        }
        return html`<button
            class="${classMap({
            'legacy-button': true,
            'header-button': true,
            'active': !this.collapsed,
        })}"
            class="legacy-button header-button"
            @click="${this.onCollapseToggled}"
        >
            ${icon}
        </button>`
    }
}

// Without this check, there's a component registry issue when developing locally.
if (!customElements.get(Container.componentName)) {
    customElements.define(Container.componentName, Container);
}

async function render({ model, el }: RenderProps<ContainerModel>) {
    const manager = document.createElement(
        Container.componentName
    ) as Container;
    manager.model = model;
    el.appendChild(manager);
}

export default { render };