import { css, html, LitElement } from "lit";
import { property } from "lit/decorators.js";

import { legacyStyles } from "./ipywidgets_styles";
import { flexStyles } from "./styles";
import { SelectOption, renderSelect } from "./utils";

export class PaletteEditor extends LitElement {
    static get componentName() {
        return `palette-editor`;
    }

    static styles = [flexStyles, legacyStyles, css``];

    @property() classesOptions: Array<SelectOption> = [
        { label: "Any", value: "any" },
        ...Array.from({ length: 7 }, (_, i) => ({
            label: `${i + 3}`,
            value: `${i + 3}`,
        })),
    ];
    @property() classes: string = "any";
    @property() colormaps: Array<string> = [];
    @property() colormap: string = "Custom";
    @property() palette: string = "";

    render() {
        return html`
            <div class="vertical-flex">
                <div class="horizontal-flex">
                    <span class="legacy-text">Colormap:</span>
                    ${renderSelect(
                        this.colormaps,
                        this.colormap,
                        this.onColormapChanged
                    )}
                    <span class="legacy-text">Number of classes:</span>
                    ${renderSelect(
                        this.classesOptions,
                        this.classes,
                        this.onClassesChanged
                    )}
                </div>
                <div class="horizontal-flex">
                    <span class="legacy-text">Palette:</span>
                    <input
                        type="text"
                        id="palette"
                        name="palette"
                        .value="${this.palette}"
                        ?disabled="${this.colormap !== "Custom"}"
                        @change="${this.onPaletteChanged}"
                    />
                </div>
                <slot></slot>
            </div>
        `;
    }

    private sendOnPaletteChangedEvent(): void {
        this.dispatchEvent(
            new CustomEvent("on-palette-changed", {
                detail: {
                    colormap: this.colormap,
                    classes: this.classes,
                    palette: this.palette,
                },
                bubbles: true,
                composed: true,
            })
        );
    }

    private onClassesChanged(event: Event): void {
        const target = event.target as HTMLInputElement;
        this.classes = target.value;
        this.sendOnPaletteChangedEvent();
    }

    private onColormapChanged(event: Event): void {
        const target = event.target as HTMLInputElement;
        this.colormap = target.value;
        this.sendOnPaletteChangedEvent();
    }

    private onPaletteChanged(event: Event): void {
        const target = event.target as HTMLInputElement;
        this.palette = target.value;
        this.sendOnPaletteChangedEvent();
    }
}

if (!customElements.get(PaletteEditor.componentName)) {
    customElements.define(PaletteEditor.componentName, PaletteEditor);
}
