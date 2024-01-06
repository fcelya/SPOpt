
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime
import pandas as pd

class ResultsAnalyzer():
    def __init__(self,instance):
        self.instance = instance
        self.all_vars = None
        self.vars = None
        self.params = None
        self.sets = None
        self.df_dict = {}

        self._load_vars()

    def _load_vars(self):
        self.all_vars = list(self.instance._decl.keys())
        # Note that no variables/params/sets should have a name ending in 'dex' and all must have a name longer than 3 characters
        self.vars = [i for i in self.all_vars if i[0]=='v' and i[-3:] != 'dex']
        self.params = [i for i in self.all_vars if i[0]=='p' and i[-3:] != 'dex']
        self.sets = [i for i in self.all_vars if i[0]=='s' and i[-3:] != 'dex']
    
    def get_vars(self):
        return self.vars
    
    def get_params(self):
        return self.params
    
    def get_sets(self):
        return self.sets

    def pprint(self, name):
        if name not in self.all_vars:
            raise ValueError(f"{name} is not a valid variable or parameter in the model. Get all valid variables or parameters through the .get_vars or .get_params methods.")
        obj = getattr(self.instance, name)
        obj.pprint()

    
    def get_df(self, name, col_names = None):
        if name not in self.all_vars:
            raise ValueError(f"{name} is not a valid variable or parameter in the model. Get all valid variables or parameters through the .get_vars or .get_params methods.")
        if name in self.df_dict.keys():
            if col_names is not None:
                if set(col_names + ['value']) == set(self.df_dict[name].columns):
                    return self.df_dict[name]
            else:
                return self.df_dict[name]
        
        obj = getattr(self.instance, name)   
        keys = getattr(self.instance, name+'_index')

        if col_names is not None:
            if len(col_names) != len(keys[1]):
                raise ValueError(f"{len(col_names)} column names have been provided but there are {len(keys[1])} values in the index. For reference, the first index is {keys[1]}")
        else:
            col_names = [f'i_{i}' for i in range(len(keys[1]))]
        
        df_values = {i:[] for i in col_names + ['value']}
        for i in keys:
            for j,c in enumerate(col_names):
                df_values[c].append(i[j])
            df_values['value'].append(obj[i].value)

        df = pd.DataFrame(df_values)
        self.df_dict[name] = df
        return df
    
    def plot_ts(self, name, time_col, col_names=None, colors=None, filter=None, inline_plot=False):
        df = self.get_df(name=name, col_names=col_names)
        if filter:
            for k in filter.keys():
                df = df[df[k]==filter[k]]
        fig = px.line(df, x=time_col, y="value", color=colors)

        if inline_plot:
            fig.show()
        else:
            fig.write_html('plot_ts_'+datetime.now().strftime('%Y%m%d%H%M%S')+'.html', auto_open=True)

    def plot_dist(self, name, filter, col_names=None, marginal='violin', colors=None, inline_plot=False):
        df = self.get_df(name=name, col_names=col_names)
        if filter:
            for k in filter.keys():
                df = df[df[k]==filter[k]]
        fig = px.histogram(df,x='value',marginal=marginal, color=colors)
        
        if inline_plot:
            fig.show()
        else:
            fig.write_html('plot_dist_'+datetime.now().strftime('%Y%m%d%H%M%S')+'.html', auto_open=True)
    
    def plot_ci(self, name, time_col, scenario_col, filter=None, col_names=None, confidence=.95, inline_plot=False):
        if confidence <=0 or confidence > 1:
            raise ValueError(f"Confidence value should be between 0 and 1")
        
        df = self.get_df(name=name, col_names=col_names)
        if filter:
            for k in filter.keys():
                df = df[df[k]==filter[k]]
        
        first_time_col = df[time_col].iloc[0]
        n_samples = len(df[df[time_col]==first_time_col])
        lower_bound = int(n_samples*(1-confidence)/2)
        upper_bound = n_samples - lower_bound

        df_plot_values = {
            'time':[],
            'lower_'+name:[],
            'upper_'+name:[],
            'mean_'+name:[],
        }
        df_agg = df.groupby([time_col, scenario_col]).agg(func={'value':'sum'}).reset_index()
        df_agg = df_agg.sort_values(by=[time_col, 'value'], ascending=[True, True])
        for t in pd.unique(df_agg[time_col]):
            values = df_agg[df_agg[time_col]==t]['value'].reset_index(drop=True)
            df_plot_values[time_col].append(t)
            df_plot_values['lower_'+name].append(values[lower_bound])
            df_plot_values['upper_'+name].append(values[upper_bound])
            df_plot_values['mean_'+name].append(values.mean())
        
        df_plot = pd.DataFrame(df_plot_values)
        fig = px.scatter(df_plot, x=time_col, y='lower_'+name)
        fig.add_trace(px.scatter(df_plot, x=time_col, y='upper_'+name).data[0])

        # Add shaded region between the two time series
        fig.add_trace(
            go.Scatter(
                x=df_plot['time'].tolist() + df_plot['time'].tolist()[::-1],
                y=df_plot['lower_'+name].tolist() + df_plot['upper_'+name].tolist()[::-1],
                fill='toself',
                fillcolor='rgba(0,100,80,0.2)',
                line=dict(color='rgba(255,255,255,0)'),
                showlegend=False
            )
        )
        fig.add_trace(
            go.Scatter(
                x=df_plot[time_col],
                y=df_plot['mean_'+name],
                mode='lines',
                name='Mean',
                line=dict(color='red', width=2)
            )
        )

        if inline_plot:
            fig.show()
        else:
            fig.write_html('plot_ci_'+datetime.now().strftime('%Y%m%d%H%M%S')+'.html', auto_open=True)
            
        

