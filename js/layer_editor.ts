import type { AnyModel, RenderProps } from '@anywidget/types';
import {
    css,
    html,
    HTMLTemplateResult,
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

export interface LayerEditorModel {
    title: string;
    type: string;
    band_names: Array<string>;
    colormaps: Array<string>;
}

interface RasterVisualizationOptions {
    bands?: Array<string>;
    gamma?: number;
    min?: number;
    max?: number;
    palette?: Array<string>;
}

interface SelectOption {
    label: string;
    value: string;
}

// interface Range {
//     name: string;
//     min?: number;
//     max?: number;
// }

// interface BandInfo {
//     name: string;
//     ranges: Array<Range>;
// }

export const flexStyles = css`
    .vertical-flex {
        display: flex;
        flex-direction: column;
    }

    .horizontal-flex {
        align-items: center;
        display: flex;
        flex-wrap: nowrap;
        gap: 32px;
    }

    input {
        width: 100%;
    }
`;

function renderSelect(options: Array<SelectOption> | Array<string>, value: string, callback: (event: Event) => void): TemplateResult {
    const newOptions = options.map(option => {
        const isString = typeof option === 'string' || option instanceof String;
        const optValue = isString ? option : option.value;
        const optLabel = isString ? option : option.label;
        return html`
            <option value=${optValue} ?selected=${value === optValue}>
                ${optLabel}
            </option>
        `;
    });
    return html`<select @change=${callback}>${newOptions}</select>`;
}

class PaletteEditor extends LitElement {
    static get componentName() {
        return `palette-editor`;
    }

    static styles = [
        flexStyles,
        legacyStyles,
        css`
            input {
                width: 100%;
            }
        `,
    ];

    @property() classesOptions: Array<SelectOption> = [
        { label: "Any", value: "any" },
        ...Array.from({ length: 7 }, (_, i) => ({
            label: (i + 3).toString(),
            value: (i + 3).toString(),
        } as SelectOption)),
    ];
    @property() classes: string = "any";
    @property() colormaps: Array<string> = [];
    @property() colormap: string = "";
    @property() palette: string = "";

    render() {
        return html`
            <div class="vertical-flex">
                <div class="horizontal-flex">
                    <span class="legacy-text">Number of classes:</span>
                    ${renderSelect(this.classesOptions, this.classes, this.onClassesChanged)}
                    <span class="legacy-text">Colormap:</span>
                    ${renderSelect(this.colormaps, this.colormap, this.onColormapChanged)}
                </div>
                <div class="horizontal-flex">
                    <span class="legacy-text">Palette:</span>
                    <input
                        type="text"
                        id="palette"
                        name="palette"
                        .value=${this.palette}
                        @change=${this.onPaletteTextChanged}
                    />
                </div>
                <slot></slot>
            </div>
        `;
    }

    private onClassesChanged(event: Event): void {
        const target = event.target as HTMLInputElement;
        this.classes = target.value;
        console.log(`Classes changed... ${this.classes}`);
    }

    private onColormapChanged(event: Event): void {
        const target = event.target as HTMLInputElement;
        this.classes = target.value;
        console.log(`Colormap changed... ${this.colormap}`);
    }

    private onPaletteTextChanged(event: Event): void {
        const target = event.target as HTMLInputElement;
        this.classes = target.value;
        console.log(`Palette changed... ${this.palette}`);
    }
}

class RasterLayerEditor extends LitElement {
    static get componentName() {
        return `raster-layer-editor-widget`;
    }

    static styles = [
        flexStyles,
        legacyStyles,
        materialStyles,
        css`    
            fieldset {
                border: none;
                margin: 0;
                padding: 0;
            }

            label {
                vertical-align: middle;
            }

            input[type="radio"] {
                margin: 0;
                vertical-align: middle;
            }

            .hidden {
                display: none;
            }

            input {
                width: 100%;
            }
        `,
    ];

    @property() colorModel: string = "";
    @property() bandNames: Array<string> = [];
    @property() selectedBands: Array<string> = [];
    @property() stretchOptions: Array<SelectOption> = [
        { label: "Custom", value: "custom" },
        { label: "1σ", value: "sigma-1" },
        { label: "2σ", value: "sigma-2" },
        { label: "3σ", value: "sigma-3" },
        { label: "90%", value: "percent-90" },
        { label: "98%", value: "percent-98" },
        { label: "100%", value: "percent-100" },
    ];
    @property() stretch: string = this.stretchOptions[0].value;
    @property() minValue: number | undefined = undefined;
    @property() maxValue: number | undefined = undefined;
    @property() minAndMaxValuesLocked: boolean = false;
    @property() opacity: number | undefined = undefined;
    @property() colorRamp: string = "";
    @property() gamma: number | undefined = undefined;
    @property() colormaps: Array<string> = [];

    // @property() options: RasterVisualizationOptions = {};

    // private getColorModel(): string {
    //     if (this.options.bands?.length == 1) {
    //         return 'grayscale';
    //     } else if (this.options.bands?.length == 3) {
    //         return 'rgb';
    //     }
    //     return '';
    // }

    render() {
        return html`
            <span>RasterLayerEditor</span>
            <form>
                <fieldset class="vertical-flex">
                    <div class="horizontal-flex">
                        ${this.renderColorModelRadio("1 band (Grayscale)", "grayscale")}
                        ${this.renderColorModelRadio("3 bands (RGB)", "rgb")}
                    </div>
                    <div id="band-selection" class="horizontal-flex">
                        ${this.selectedBands.map(band => {
            return this.renderBandSelection(band);
        })}
                    </div>
                    <div class="horizontal-flex">
                        <span class="legacy-text">Stretch:</span>
                        ${this.renderStretchSelection()}
                        <button
                            class="legacy-button"
                            @click="${this.onRefreshButtonClicked}"
                        >
                            <span class="material-symbols-outlined">&#xe627;</span>
                        </button>
                    </div>
                    <div class="horizontal-flex">
                        <span class="legacy-text">Range:</span>
                        <input
                            type="text"
                            id="min"
                            name="min"
                            .value="${this.minValue}"
                            @change="${this.onMinTextChanged}"
                            ?disabled="${this.minAndMaxValuesLocked}"
                        />
                        <span class="legacy-text">to</span>
                        <input
                            type="text"
                            id="max"
                            name="max"
                            .value="${this.maxValue}"
                            @change="${this.onMaxTextChanged}"
                            ?disabled="${this.minAndMaxValuesLocked}"
                        />
                    </div>
                    <div class="horizontal-flex">
                        <span class="legacy-text">Opacity:</span>
                        <input
                            type="range"
                            id="opacity"
                            name="opacity"
                            min="0"
                            max="1.0"
                            step="0.01"
                            .value=${this.opacity}
                            @input=${this.onOpacityChanged}
                            @change=${this.onOpacityChanged}
                        />
                        <span class="legacy-text">${this.opacity}</span>
                    </div>
                    <div class="horizontal-flex ${this.hiddenIf(this.colorModel !== "grayscale")}">
                        ${this.renderColorRampRadio("Palette", "palette")}
                        ${this.renderColorRampRadio("Gamma", "gamma")}
                    </div>
                    <palette-editor
                        class="${this.hiddenIf(this.colorRamp !== "palette" || this.colorModel !== "grayscale")}"
                        .colormaps="${this.colormaps}"
                    >

                    </palette-editor>
                    <div class="horizontal-flex ${this.hiddenIf(!(this.colorRamp === "gamma" || this.colorModel === "rgb"))}">
                        <span class="legacy-text">Gamma:</span>
                        <input
                            type="range"
                            id="opacity"
                            name="opacity"
                            min="0.1"
                            max="10"
                            step="0.01"
                            .value=${this.gamma}
                            @input=${this.onGammaChanged}
                            @change=${this.onGammaChanged}
                        />
                        <span class="legacy-text">${this.gamma}</span>
                    </div>
                </fieldset>
            </form>
        `;
    }

    private hiddenIf(value: boolean): string {
        return value ? 'hidden' : '';
    }

    private renderColorModelRadio(label: string, value: string): TemplateResult {
        return html`
            <span>
                <input
                    type="radio"
                    id="${value}"
                    name="color-model"
                    value="${value}"
                    @click="${this.onColorModelChanged}"
                    ?checked=${this.colorModel === value}
                />
                <label class="legacy-text">${label}</label>
            </span>
        `;
    }

    private renderColorRampRadio(label: string, value: string): TemplateResult {
        return html`
            <span>
                <input
                    type="radio"
                    id="${value}"
                    name="color-ramp"
                    value="${value}"
                    @click="${this.onColorRampChanged}"
                    ?checked=${this.colorRamp === value}
                />
                <label class="legacy-text">${label}</label>
            </span>
        `;
    }

    private onColorRampChanged(event: Event): void {
        const target = event.target as HTMLInputElement;
        this.colorRamp = target.value;
        // if (this.colorRamp === "gamma") {
        //     // this.selectedBands = Array.from([this.bandNames[0]]);
        // } else if (this.colorRamp == "palette") {
        //     // this.selectedBands = Array.from([this.bandNames[0], this.bandNames[0], this.bandNames[0]]);
        // }
    }

    private renderBandSelection(value: string): TemplateResult {
        const options = this.bandNames.map((name) => ({ label: name, value: name } as SelectOption));
        return renderSelect(options, value, this.onBandSelectionChanged);
    }

    private renderStretchSelection(): TemplateResult {
        return renderSelect(this.stretchOptions, this.stretch, this.onStretchChanged);
    }

    private onRefreshButtonClicked(event: Event): void {
        console.log("Refresh button clicked...");
    }

    private onOpacityChanged(event: Event): void {
        console.log("Opacity changed...");
        const target = event.target as HTMLInputElement;
        this.opacity = target.valueAsNumber;
    }

    private onGammaChanged(event: Event): void {
        console.log("Gamma changed...");
        const target = event.target as HTMLInputElement;
        this.gamma = target.valueAsNumber;
    }

    private onMinTextChanged(event: Event): void {
        console.log("Min text changed...");
    }

    private onMaxTextChanged(event: Event): void {
        console.log("Max text changed...");
    }

    private onStretchChanged(event: Event): void {
        this.stretch = (event.target as HTMLInputElement).value;
        if (this.stretch === 'custom') {
            this.minAndMaxValuesLocked = false;
        } else {
            this.minAndMaxValuesLocked = true;
            this.minValue = undefined;
            this.maxValue = undefined;
        }
        this.dispatchEvent(new CustomEvent('calculate-band-stats', {}));
    }

    private onBandSelectionChanged(event: Event): void {
        const target = event.target as HTMLInputElement;
        console.log(`onBandSelectionChanged ${target.value}`);
        this.selectedBands = this.getSelectedBands();
    }

    private onColorModelChanged(event: Event): void {
        const target = event.target as HTMLInputElement;
        this.colorModel = target.value;
        if (this.colorModel === "grayscale") {
            this.selectedBands = Array.from([this.bandNames[0]]);
        } else if (this.colorModel == "rgb") {
            this.selectedBands = Array.from([this.bandNames[0], this.bandNames[0], this.bandNames[0]]);
        }
    }

    private getSelectedBands(): Array<string> {
        const container = this.renderRoot?.querySelector(`#band-selection`) as HTMLDivElement;
        // const set = new Set<string>();
        return Array.from(container.querySelectorAll('select')).map(input => (input as unknown as HTMLInputElement).value);
        // inputs.forEach(input => {
        //     set.add((input as unknown as HTMLInputElement).value);
        // });
        // return Array.from(set.values());
    }
}

class VectorLayerEditor extends LitElement {
    static get componentName() {
        return `vector-layer-editor-widget`;
    }

    static styles = [
        legacyStyles,
        css`    

        `,
    ];

    render() {
        return html`
            <span>VectorLayerEditor</span>
        `;
    }
}

export class LayerEditor extends LitElement {
    static get componentName() {
        return `layer-editor-widget`;
    }

    static styles = [
        legacyStyles,
        css`    
            .hidden {
                display: none;
            }
            
            .confirm-button {
                padding: 0 20px;
            }

            .confirm-button-row {
                display: flex;
                gap: 4px;
                margin-top: 4px;
            }

            .editor-container {
                max-width: 350px;
            }

            input {
                width: 100%;
            }
        `,
    ];

    private _model: AnyModel<LayerEditorModel> | undefined = undefined;
    private static modelNameToViewName = new Map<
        keyof LayerEditorModel,
        keyof LayerEditor
    >([
        ['title', 'title'],
        ['type', 'type'],
        ['band_names', 'bandNames'],
        ['colormaps', 'colormaps'],
    ]);
    private static viewNameToModelName = reverseMap(this.modelNameToViewName);

    set model(model: AnyModel<LayerEditorModel>) {
        this._model = model;
        for (const [modelKey, widgetKey] of LayerEditor.modelNameToViewName) {
            if (widgetKey) {
                // Get initial values from the Python model.
                (this as any)[widgetKey] = model.get(modelKey);
                // Listen for updates to the model.
                model.on(`change:${modelKey}`, () => {
                    (this as any)[widgetKey] = model.get(modelKey);
                });
            }
        }
        this.registerCustomMessageHandlers();
    }

    private registerCustomMessageHandlers(): void {
        this._model?.on("msg:custom", (msg: any) => {
            console.log('On msg:custom');
            console.log(msg);
            if ("bandstats" in msg) {
                this.handleBandstatsResponse(msg);
            }
            // if ("assets" in msg) {
            //     handleAssetRequestSuccess(msg["id"], msg["assets"]);
            // } else {
            //     handleAssetRequestFailure(msg["id"], msg["error"]);
            // }
        });
    }

    @property() title: string = "";
    @property() type: string = "";
    @property() bandNames: Array<string> = [];
    @property() colormaps: Array<string> = [];

    render() {
        return html`
            <widget-container
                .title="${this.title}"
                @close-clicked="${this.onCloseButtonClicked}"
            >
                <div class="editor-container">
                    <vector-layer-editor-widget
                        class="${this.type == 'vector' ? '' : 'hidden'}"
                    >
                    </vector-layer-editor-widget>
                    <raster-layer-editor-widget
                        class="${this.type == 'raster' ? '' : 'hidden'}"
                        .bandNames="${this.bandNames}"
                        .colormaps="${this.colormaps}"
                        @calculate-band-stats="${this.calculateBandStats}"
                    >
                    </raster-layer-editor-widget>
                    <div
                        class="${this.type == '' ? '' : 'hidden'}"
                    >
                        <span>Vis params are uneditable</span>
                    </div>
                </div>
                <div class="confirm-button-row">
                    <button
                        class="legacy-button primary confirm-button"
                    >
                        Import
                    </button>
                    <button
                        class="legacy-button confirm-button"
                    >
                        Apply
                    </button>
                </div>
            </widget-container>
        `;
    }

    // private onFeatureCheckboxEvent(event: Event) {
    //     const target = event.target as HTMLInputElement;
    //     this.expandObjects = target.checked;
    // }

    private onCloseButtonClicked(_: Event) {
        this._model?.send({ "type": "click", "id": "close" });
    }

    private calculateBandStats(event: Event) {
        console.log(`calculateBandStats:`);
        console.log(event);

        const rasterEditor = this.renderRoot?.querySelector('raster-layer-editor-widget') as RasterLayerEditor;
        this._model?.send({
            "type": "calculate", "id": "band-stats", "detail": {
                bands: rasterEditor.selectedBands,
                stretch: rasterEditor.stretch,
            },
        });
    }

    private handleBandstatsResponse(response: any): void {
        const rasterEditor = this.renderRoot?.querySelector('raster-layer-editor-widget') as RasterLayerEditor;
        if (response.bandstats.stretch === rasterEditor.stretch) {
            rasterEditor.minValue = response.bandstats.min;
            rasterEditor.maxValue = response.bandstats.max;
        }
    }

    updated(changedProperties: PropertyValues<LayerEditor>) {
        // Update the model properties so they're reflected in Python.
        for (const [viewProp, _] of changedProperties) {
            const castViewProp = viewProp as keyof LayerEditor;
            if (LayerEditor.viewNameToModelName.has(castViewProp)) {
                const modelProp = LayerEditor.viewNameToModelName.get(castViewProp);
                this._model?.set(modelProp as any, this[castViewProp] as any);
            }
        }
        this._model?.save_changes();
    }
}

// Without this check, there's a component registry issue when developing locally.
if (!customElements.get(PaletteEditor.componentName)) {
    customElements.define(PaletteEditor.componentName, PaletteEditor);
}
if (!customElements.get(RasterLayerEditor.componentName)) {
    customElements.define(RasterLayerEditor.componentName, RasterLayerEditor);
}
if (!customElements.get(VectorLayerEditor.componentName)) {
    customElements.define(VectorLayerEditor.componentName, VectorLayerEditor);
}
if (!customElements.get(LayerEditor.componentName)) {
    customElements.define(LayerEditor.componentName, LayerEditor);
}

async function render({ model, el }: RenderProps<LayerEditorModel>) {
    const widget = document.createElement(
        LayerEditor.componentName,
    ) as LayerEditor;
    widget.model = model;
    el.appendChild(widget);
}

export default { render };
